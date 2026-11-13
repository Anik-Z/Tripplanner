
import uuid
from contextvars import ContextVar
from typing import Any

RequestId = str

request_id_context: ContextVar[RequestId] = ContextVar(
    "request_id",
    default="",
)


def get_request_id() -> str:
    """Get the request ID associated with the current execution context."""
    return request_id_context.get()


class RequestIDMiddleware:
    """ASGI middleware that attaches a unique request ID to every request."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())

        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)

        async def send_with_request_id(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                message["headers"] = headers

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(token)
