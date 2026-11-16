from pathlib import Path
from unittest.mock import patch
import httpx
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[2] / 'frontend' / 'app.py'

def fake_api(method, url, **kwargs):
    request = httpx.Request(method, url)
    if url.endswith('/profiles'):
        data = [{'id':'student_a', 'name':'Student A', 'scenario':'Demo'}]
    elif url.endswith('/vitals'):
        data = {'current':None, 'history':[], 'sleep':[], 'summary':{'data_stale':True}}
    elif url.endswith('/chat'):
        data = {'reply':'Mock response', 'safety_route':'ordinary_support', 'latency_ms':1, 'sources':[], 'tool_trace':[], 'simulated_data_used':False}
    else:
        data = {'saved':True}
    return httpx.Response(200, json=data, request=request)

def test_dashboard_comparison_and_mood():
    with patch('httpx.request', side_effect=fake_api) as calls:
        app = AppTest.from_file(str(APP)).run()
        assert not app.exception
        app.checkbox[0].check().run()
        app.text_area[0].set_value('Exam tomorrow').run()
        next(b for b in app.button if b.label == 'Compare A/B/C').click().run()
        posts = [c.kwargs['json'] for c in calls.call_args_list if c.args[1].endswith('/chat')]
        assert len(posts) == 3
        assert len({p['session_id'] for p in posts}) == 3
        assert {p['mode'] for p in posts} == {'text_only','current_vitals','full_context'}
        assert {p['message'] for p in posts} == {'Exam tomorrow'}
        next(b for b in app.button if b.label == 'Save check-in').click().run()
        assert app.success[0].value == 'Check-in saved'
        assert not app.exception

def test_frontend_shows_api_error():
    with patch('httpx.request', side_effect=httpx.ConnectError('server unavailable')):
        app = AppTest.from_file(str(APP)).run()
        assert not app.exception
        assert 'server unavailable' in app.error[0].value


def test_dashboard_with_real_seeded_api_and_live_telemetry(tmp_path):
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient
    from mindsync.config import Settings
    from mindsync.platform.api import create_app

    with TestClient(create_app(Settings(db_path=tmp_path/'dashboard.db'))) as client:
        client.post('/telemetry', json={
            'profile_id': 'student_a', 'measured_at': datetime.now(timezone.utc).isoformat(),
            'heart_rate_bpm': 75, 'spo2_percent': 98,
            'respiratory_rate_per_min': 15, 'activity_level': .2})

        def request(method, url, **kwargs):
            from urllib.parse import urlsplit
            kwargs.pop('timeout', None)
            return client.request(method, urlsplit(url).path, **kwargs)

        with patch('httpx.request', side_effect=request):
            app = AppTest.from_file(str(APP)).run()
            assert not app.exception
            assert len(app.metric) == 4
            app.chat_input[0].set_value('I have an exam tomorrow').run()
            assert not app.exception
            assert len(app.chat_message) == 2
            app.selectbox[1].select('B · Current vitals').run()
            app.chat_input[0].set_value('Please help').run()
            assert 'Enable consent' in app.error[0].value
            app.checkbox[0].check().run()
            app.chat_input[0].set_value('Please help').run()
            assert not app.exception
            assert len(app.chat_message) == 2
