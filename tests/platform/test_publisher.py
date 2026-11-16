import sys
from unittest.mock import patch

import httpx
import pytest

from mindsync.simulator.publisher import main


def test_finite_failure_has_nonzero_status_and_no_false_retry(capsys):
    with patch.object(sys, 'argv', ['publisher', '--count', '1']), \
         patch('httpx.Client.post', side_effect=httpx.ConnectError('offline')):
        assert main() == 1
    output = capsys.readouterr().out
    assert 'No attempts remain' in output
    assert 'Next attempt' not in output


def test_publisher_retries_and_reports_partial_failure(capsys):
    response = httpx.Response(200, request=httpx.Request('POST', 'http://localhost/telemetry'))
    with patch.object(sys, 'argv', ['publisher', '--count', '2']), \
         patch('httpx.Client.post', side_effect=[httpx.ConnectError('offline'), response]) as post, \
         patch('mindsync.simulator.publisher.time.sleep') as sleep:
        assert main() == 1
    assert post.call_count == 2
    sleep.assert_called_once_with(5)
    assert 'Published simulated reading' in capsys.readouterr().out


def test_negative_count_rejected():
    with patch.object(sys, 'argv', ['publisher', '--count', '-1']), pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


def test_interrupt_exits_gracefully(capsys):
    with patch.object(sys, 'argv', ['publisher']), \
         patch('httpx.Client.post', side_effect=KeyboardInterrupt):
        assert main() == 130
    assert 'Simulator stopped' in capsys.readouterr().out
