from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from just_bash import Bash


@contextmanager
def local_http_server() -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._write_response()

        def do_POST(self) -> None:
            self._write_response()

        def _write_response(self) -> None:
            length = int(self.headers.get("content-length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            payload = {
                "method": self.command,
                "path": self.path,
                "xInjected": self.headers.get("x-injected"),
                "body": body,
            }
            encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, name="just-py-bash-network-example", daemon=True)
    thread.start()
    try:
        address = server.server_address
        host = str(address[0])
        port = int(address[1])
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2.0)
        server.server_close()


def main() -> None:
    with local_http_server() as base_url:
        with Bash(
            network={
                "allowedUrlPrefixes": [
                    {
                        "url": base_url,
                        "transform": [{"headers": {"X-Injected": "from-network-config"}}],
                    }
                ],
                "allowedMethods": ["GET", "HEAD", "POST"],
            }
        ) as bash:
            get_result = bash.exec(
                f"curl -s {base_url}/inspect | jq -r '.method + \" \" + .path + \" \" + .xInjected'",
            )
            post_result = bash.exec(
                f"curl -s -X POST -d 'alpha=beta' {base_url}/inspect | jq -r '.method + \" \" + .body'",
            )

    print("=== Network access ===")
    print(get_result.stdout, end="")
    print(post_result.stdout, end="")


if __name__ == "__main__":
    main()
