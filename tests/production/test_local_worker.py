from unittest.mock import Mock, patch

import requests

from backend.tools.local_worker import deliver


def test_delivery_acknowledges_only_after_worker_success():
    message = Mock(data=b'{"event_id":"example"}', message_id='message-1')
    with patch('backend.tools.local_worker.requests.post') as post:
        deliver('activity', message)
    assert post.call_args.args[0] == 'http://127.0.0.1:8003/internal/pubsub/activity'
    assert post.call_args.kwargs['json']['message']['data'] == 'eyJldmVudF9pZCI6ImV4YW1wbGUifQ=='
    message.ack.assert_called_once()
    message.nack.assert_not_called()


def test_delivery_retries_when_worker_fails():
    message = Mock(data=b'{}', message_id='message-2')
    with patch('backend.tools.local_worker.requests.post') as post:
        post.return_value.raise_for_status.side_effect = requests.HTTPError('503')
        deliver('activity', message)
    message.nack.assert_called_once()
    message.ack.assert_not_called()
