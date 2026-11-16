"""Repeatable local HTTP smoke test; no cloud services or external LLMs."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[2]


def available_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_for_health(process, url, log_path):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(log_path.read_text())
        try:
            response = httpx.get(url, timeout=1)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise AssertionError(f'Server did not become healthy: {log_path.read_text()}')


def test_live_servers_publisher_and_modes(tmp_path):
    api_port = available_port()
    ui_port = available_port()
    while ui_port == api_port:
        ui_port = available_port()
    base_url = f'http://127.0.0.1:{api_port}'
    env = dict(os.environ, MINDSYNC_DB_PATH=str(tmp_path / 'live.db'),
               MINDSYNC_AGENT='mock', MINDSYNC_SEED_DEMO='true',
               MINDSYNC_API_URL=base_url)
    # Preserve source imports even when the test process uses pytest's pythonpath.
    env['PYTHONPATH'] = str(ROOT / 'src')
    commands = [
        ([sys.executable, '-m', 'uvicorn', 'mindsync.platform.api:app',
          '--host', '127.0.0.1', '--port', str(api_port)], base_url + '/health'),
        ([sys.executable, '-m', 'streamlit', 'run', 'frontend/app.py',
          '--server.headless=true', '--server.address=127.0.0.1',
          '--server.port', str(ui_port), '--browser.gatherUsageStats=false'],
         f'http://127.0.0.1:{ui_port}/_stcore/health'),
    ]
    processes = []
    logs = []
    try:
        for index, (command, health_url) in enumerate(commands):
            log_path = tmp_path / f'server-{index}.log'
            log = log_path.open('w')
            logs.append(log)
            process = subprocess.Popen(command, cwd=ROOT, env=env,
                                       stdout=log, stderr=subprocess.STDOUT)
            processes.append(process)
            wait_for_health(process, health_url, log_path)
        published = subprocess.run(
            [sys.executable, '-m', 'mindsync.simulator.publisher',
             '--url', base_url, '--count', '1'], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=15, check=True)
        assert 'Published simulated reading' in published.stdout
        with httpx.Client(base_url=base_url, timeout=5) as client:
            data = client.get('/profiles/student_a/vitals')
            data.raise_for_status()
            assert data.json()['current']['simulated'] is True
            for mode, expected_calls in [('text_only', 0), ('current_vitals', 1), ('full_context', 2)]:
                result = client.post('/chat', json={
                    'session_id': mode, 'profile_id': 'student_a',
                    'message': 'I have an exam tomorrow', 'mode': mode,
                    'consent_to_use_vitals': True})
                result.raise_for_status()
                assert result.json()['mode'] == mode
                assert len(result.json()['tool_trace']) == expected_calls
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for log in logs:
            log.close()
