import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import itertools

MESSAGES = [
    {
        "id": 1,
        "channel": "webchat",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "customer": {
            "id": "CUST-1001",
            "name": "홍길동",
            "email": "hong@example.com",
            "phone": "+82-10-1111-2222",
        },
        "text": "배송이 언제 도착하나요?",
        "metadata": {"language": "ko", "pii": ["email", "phone"]},
    },
    {
        "id": 2,
        "channel": "webchat",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "customer": {
            "id": "CUST-1002",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+82-10-3333-4444",
        },
        "text": "환불 절차가 어떻게 되나요?",
        "metadata": {"language": "ko", "pii": ["email", "phone"]},
    },
]
_lock = threading.Lock()
_id_counter = itertools.count(start=len(MESSAGES) + 1)


class WebChatHandler(BaseHTTPRequestHandler):
    server_version = "MockWebChat/0.1"

    def _set_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        # suppress default stdout noise
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/messages":
            self._set_headers(404)
            self.wfile.write(b"{}")
            return

        query = parse_qs(parsed.query)
        after = int(query.get("after", [0])[0])
        with _lock:
            data = [m for m in MESSAGES if m["id"] > after]
        payload = {"messages": data}
        self._set_headers(200)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/messages":
            self._set_headers(404)
            self.wfile.write(b"{}")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(b"{\"error\":\"invalid json\"}")
            return

        with _lock:
            message = {
                "id": payload.get("id") or next(_id_counter),
                "channel": payload.get("channel", "webchat"),
                "timestamp": payload.get("timestamp")
                or datetime.utcnow().isoformat() + "Z",
                "customer": payload.get("customer", {}),
                "text": payload.get("text", ""),
                "metadata": payload.get("metadata", {}),
            }
            MESSAGES.append(message)
        self._set_headers(201)
        self.wfile.write(json.dumps(message, ensure_ascii=False).encode("utf-8"))


def run_server(port: int = 5001) -> None:
    server = HTTPServer(("0.0.0.0", port), WebChatHandler)
    print(f"Mock WebChat server listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
