import asyncio
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from mindsync.config import Settings
from mindsync.contracts import AgentOutput, ChatRequest, Mode, VitalReading
from mindsync.platform.api import create_app
from mindsync.platform.context_service import SQLiteContextProvider, RestrictedContextProvider
from mindsync.simulator.seed import seed
from mindsync.storage.database import connect
from mindsync.storage.migrations import migrate
from mindsync.storage.repository import Repository

NOW = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)

@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'test.db'
    migrate(path)
    seed(path, now=NOW)
    return path

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(db_path=tmp_path/'api.db'))) as client:
        yield client

def request_body(**updates):
    return dict(session_id='test', profile_id='student_a', message='I have a difficult exam tomorrow', mode='text_only', **updates)

def test_migrations_fresh_and_idempotent(tmp_path):
    path = tmp_path/'fresh.db'
    migrate(path)
    migrate(path)
    with connect(path) as conn:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'profiles', 'vital_samples', 'daily_sleep', 'check_ins', 'schema_migrations'} <= names
        assert conn.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO daily_sleep VALUES ('missing', '2026-01-01', 8)")

def test_seed_deterministic_and_idempotent(db, tmp_path):
    other = tmp_path/'other.db'
    migrate(other)
    seed(other, now=NOW)
    seed(db, now=NOW+timedelta(days=1))
    with connect(db) as a, connect(other) as b:
        for table in ('profiles', 'vital_samples', 'daily_sleep'):
            assert [tuple(r) for r in a.execute(f'SELECT * FROM {table}')] == [tuple(r) for r in b.execute(f'SELECT * FROM {table}')]
        assert a.execute("SELECT COUNT(*) FROM vital_samples WHERE profile_id='student_a'").fetchone()[0] == 168

def test_exact_statistics(tmp_path):
    path = tmp_path/'stats.db'
    migrate(path)
    with connect(path) as conn:
        conn.execute("INSERT INTO profiles VALUES ('p', 'P', 'test')")
        for day, hours in [(7,8), (6,8), (5,8), (4,8), (3,5), (2,5), (1,5)]:
            conn.execute('INSERT INTO daily_sleep VALUES (?,?,?)', ('p', (NOW-timedelta(days=day)).date().isoformat(), hours))
    repo = Repository(path)
    for hour, hr in [(0,60), (1,80), (2,None)]:
        repo.save_vital(VitalReading(profile_id='p', measured_at=NOW-timedelta(hours=hour), heart_rate_bpm=hr))
    context = SQLiteContextProvider(repo, clock=lambda: NOW)
    result = context.get_history_summary('p')
    assert result.sample_count == 3
    assert result.mean_heart_rate_bpm == 70
    assert result.earlier_sleep_avg_hours == 8
    assert result.recent_sleep_avg_hours == 5
    assert result.missing_fraction == pytest.approx(1-2/(168*4))
    assert not result.data_stale

def test_missing_stale_empty_and_future(db):
    repo = Repository(db)
    context = SQLiteContextProvider(repo, clock=lambda: NOW)
    assert context.get_current_vitals('student_a').simulated
    assert context.get_current_vitals('student_c') is None
    assert context.get_history_summary('student_c').data_stale
    empty = context.get_history_summary('absent')
    assert empty.sample_count == 0 and empty.mean_heart_rate_bpm is None
    assert empty.missing_fraction == 1 and empty.data_stale
    repo.save_vital(VitalReading(profile_id='student_c', measured_at=NOW+timedelta(days=1), heart_rate_bpm=70))
    assert context.get_current_vitals('student_c') is None
    with pytest.raises(ValueError):
        context.get_history_summary('student_a', 0)

def test_valid_telemetry_utc_and_duplicate(client):
    stamp = datetime.now(timezone(timedelta(hours=5, minutes=30)))-timedelta(seconds=1)
    packet = {'profile_id':'student_a', 'measured_at':stamp.isoformat(), 'heart_rate_bpm':77}
    assert client.post('/telemetry', json=packet).status_code == 200
    assert client.post('/telemetry', json=packet).status_code == 200
    current = client.get('/profiles/student_a/vitals').json()['current']
    assert current['heart_rate_bpm'] == 77 and current['simulated']
    assert current['measured_at'].endswith('Z') or current['measured_at'].endswith('+00:00')

@pytest.mark.parametrize('changes', [
    {'heart_rate_bpm':-1}, {'spo2_percent':101}, {'respiratory_rate_per_min':100},
    {'activity_level':2}, {'measured_at':'2026-11-16T12:00:00'}, {'simulated':False},
    {'measured_at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}, {'unknown':1},
])
def test_invalid_telemetry(client, changes):
    packet = {'profile_id':'student_a', 'measured_at':datetime.now(timezone.utc).isoformat(), 'heart_rate_bpm':70}
    packet.update(changes)
    assert client.post('/telemetry', json=packet).status_code == 422

@pytest.mark.parametrize('value', [float('nan'), float('inf')])
def test_nonfinite(value):
    with pytest.raises(ValidationError):
        VitalReading(profile_id='p', measured_at=NOW, heart_rate_bpm=value)

@pytest.mark.parametrize('mode', list(Mode))
def test_capabilities(db, mode):
    raw = SQLiteContextProvider(Repository(db), clock=lambda: NOW)
    req = ChatRequest(session_id='s', profile_id='student_a', message='hello', mode=mode, consent_to_use_vitals=True)
    scoped = RestrictedContextProvider(raw, req)
    for target in ('student_b', 'missing'):
        with pytest.raises(PermissionError):
            scoped.get_current_vitals(target)
        with pytest.raises(PermissionError):
            scoped.get_history_summary(target)
    if mode == Mode.TEXT_ONLY:
        with pytest.raises(PermissionError):
            scoped.get_current_vitals('student_a')
    else:
        assert scoped.get_current_vitals('student_a')
    if mode != Mode.FULL_CONTEXT:
        with pytest.raises(PermissionError):
            scoped.get_history_summary('student_a')
    else:
        assert scoped.get_history_summary('student_a').sample_count == 168

@pytest.mark.parametrize('mode', ['current_vitals', 'full_context'])
def test_consent(client, mode):
    body = request_body()
    body['mode'] = mode
    assert client.post('/chat', json=body).status_code == 403
    body['consent_to_use_vitals'] = True
    assert client.post('/chat', json=body).status_code == 200

def test_unknown_profiles(client):
    body = request_body()
    body['profile_id'] = 'missing'
    assert client.post('/chat', json=body).status_code == 404
    assert client.get('/profiles/missing/vitals').status_code == 404
    assert client.post('/telemetry', json={'profile_id':'missing', 'measured_at':NOW.isoformat()}).status_code == 404

@pytest.mark.parametrize('message', ['I want to kill myself', 'I have chest pain', 'I can’t breathe', 'I took too many pills', 'I am suicidal'])
def test_safety_bypasses_agent(tmp_path, message):
    async def must_not_run(*args):
        pytest.fail('Urgent request reached agent')
    with TestClient(create_app(Settings(db_path=tmp_path/'safe.db'), agent=must_not_run)) as client:
        body = request_body()
        body['message'] = message
        response = client.post('/chat', json=body)
        assert response.status_code == 200
        result = response.json()
        assert result['safety_route'] == 'urgent_support'
        assert result['tool_trace'] == [] and not result['simulated_data_used']

def test_mock_and_check_ins(client):
    assert client.get('/health').json()['agent'] == 'mock'
    assert len(client.get('/profiles').json()) == 3
    result = client.post('/chat', json=request_body()).json()
    assert result['safety_route'] == 'ordinary_support' and result['tool_trace'] == []
    assert not result['simulated_data_used']
    body = request_body()
    body.update(mode='full_context', consent_to_use_vitals=True)
    result = client.post('/chat', json=body).json()
    assert len(result['tool_trace']) == 2 and result['simulated_data_used']
    assert client.post('/profiles/student_a/check-ins', json={'mood':4, 'note':'Done'}).status_code == 201
    assert client.get('/profiles/student_a/check-ins').json()[0]['note'] == 'Done'
    assert client.post('/profiles/student_a/check-ins', json={'mood':8}).status_code == 422
    assert client.post('/chat', json={**body, 'message':'   '}).status_code == 422

def test_agent_receives_restricted_context(tmp_path):
    async def spy(req, provider):
        with pytest.raises(PermissionError):
            provider.get_current_vitals(req.profile_id)
        return AgentOutput(reply='Injected agent')
    with TestClient(create_app(Settings(db_path=tmp_path/'spy.db'), agent=spy)) as client:
        assert client.post('/chat', json=request_body()).json()['reply'] == 'Injected agent'

@pytest.mark.parametrize('failure,expected', [('error',502), ('timeout',504), ('invalid',502)])
def test_agent_failures(tmp_path, failure, expected):
    async def agent(*args):
        if failure == 'timeout':
            await asyncio.sleep(1)
        if failure == 'error':
            raise RuntimeError('private details')
        return {'invalid':'output'}
    with TestClient(create_app(Settings(db_path=tmp_path/'fail.db', agent_timeout_seconds=.01), agent=agent)) as client:
        response = client.post('/chat', json=request_body())
        assert response.status_code == expected
        assert 'private details' not in response.text
