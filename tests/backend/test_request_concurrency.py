import asyncio
import json

import pytest

from backend.app.api.middleware import BoundaryMiddleware


def _scope():
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/projects",
        "raw_path": b"/api/v1/projects",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1),
        "server": ("test", 80),
        "state": {},
    }


def _complete_receive(body=b"{}", called=None):
    delivered = False

    async def receive():
        nonlocal delivered
        if called is not None:
            called.append(True)
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return receive


def _send_to(messages):
    async def send(message):
        messages.append(message)

    return send


def test_body_concurrency_limit_rejects_before_receiving_and_releases_after_completion():
    async def scenario():
        entered = 0
        all_entered = asyncio.Event()
        release = asyncio.Event()

        async def app(scope, receive, send):
            nonlocal entered
            message = await receive()
            assert message["body"] == b"{}"
            entered += 1
            if entered == 2:
                all_entered.set()
            await release.wait()
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = BoundaryMiddleware(app, max_buffered_requests=2)
        first_messages, second_messages = [], []
        first = asyncio.create_task(middleware(_scope(), _complete_receive(), _send_to(first_messages)))
        second = asyncio.create_task(middleware(_scope(), _complete_receive(), _send_to(second_messages)))
        await asyncio.wait_for(all_entered.wait(), 1)

        overloaded_messages = []
        receive_calls = []
        await middleware(_scope(), _complete_receive(called=receive_calls), _send_to(overloaded_messages))
        assert receive_calls == []
        assert overloaded_messages[0]["status"] == 503
        headers = dict(overloaded_messages[0]["headers"])
        assert headers[b"retry-after"] == b"1"
        payload = json.loads(overloaded_messages[1]["body"])
        assert payload["error"]["code"] == "REQUEST_OVERLOADED"

        release.set()
        await asyncio.gather(first, second)
        assert first_messages[0]["status"] == 204
        assert second_messages[0]["status"] == 204

        followup = []
        await middleware(_scope(), _complete_receive(), _send_to(followup))
        assert followup[0]["status"] == 204

    asyncio.run(scenario())


def test_body_concurrency_slot_is_released_after_receive_cancellation():
    async def scenario():
        receive_started = asyncio.Event()

        async def app(scope, receive, send):
            await receive()
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        async def blocked_receive():
            receive_started.set()
            await asyncio.Event().wait()

        middleware = BoundaryMiddleware(app, max_buffered_requests=1)
        task = asyncio.create_task(middleware(_scope(), blocked_receive, _send_to([])))
        await asyncio.wait_for(receive_started.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        messages = []
        await middleware(_scope(), _complete_receive(), _send_to(messages))
        assert messages[0]["status"] == 204

    asyncio.run(scenario())


def test_body_concurrency_slot_is_released_after_downstream_error():
    async def scenario():
        calls = 0

        async def app(scope, receive, send):
            nonlocal calls
            await receive()
            calls += 1
            if calls == 1:
                raise RuntimeError("synthetic downstream failure")
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = BoundaryMiddleware(app, max_buffered_requests=1)
        failed = []
        await middleware(_scope(), _complete_receive(), _send_to(failed))
        assert failed[0]["status"] == 500

        followup = []
        await middleware(_scope(), _complete_receive(), _send_to(followup))
        assert followup[0]["status"] == 204

    asyncio.run(scenario())


def test_body_concurrency_limit_must_be_positive():
    with pytest.raises(ValueError):
        BoundaryMiddleware(object(), max_buffered_requests=0)
