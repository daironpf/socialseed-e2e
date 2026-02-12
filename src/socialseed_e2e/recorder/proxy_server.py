"""Recording proxy for socialseed-e2e."""

import json
import logging
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional
from urllib.parse import urlparse

import requests

from socialseed_e2e.recorder.models import RecordedInteraction, RecordedSession

logger = logging.getLogger(__name__)


class RecordingProxyHandler(BaseHTTPRequestHandler):
    """Handler for recording proxy requests."""

    session: Optional[RecordedSession] = None

    def do_HEAD(self):
        """Handle HEAD requests."""
        self._handle_request("HEAD")

    def do_GET(self):
        """Handle GET requests."""
        self._handle_request("GET")

    def do_POST(self):
        """Handle POST requests."""
        self._handle_request("POST")

    def do_PUT(self):
        """Handle PUT requests."""
        self._handle_request("PUT")

    def do_DELETE(self):
        """Handle DELETE requests."""
        self._handle_request("DELETE")

    def do_PATCH(self):
        """Handle PATCH requests."""
        self._handle_request("PATCH")

    def _handle_request(self, method: str):
        """Handle incoming request, forward it, and record."""
        # Get request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Prepare headers for forwarding (remove proxy-specific headers)
        headers = {
            k: v for k, v in self.headers.items() if k.lower() not in ["host", "proxy-connection"]
        }

        # Forward the request
        # In a real proxy, the path is the full URL
        url = self.path
        if not urlparse(url).scheme:
            # If it's not a full URL, it might be a relative path (if used as a gateway)
            # For this simple recorder, we expect absolute URLs or we need a target host
            self.send_error(400, "Proxy requires absolute URLs")
            return

        start_time = time.time()
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                allow_redirects=False,
                verify=False,
            )
            duration_ms = (time.time() - start_time) * 1000

            # Record the interaction
            if self.session:
                interaction = RecordedInteraction(
                    timestamp=datetime.now(),
                    method=method,
                    url=url,
                    request_headers=dict(self.headers),
                    request_body=self._try_parse_body(body, self.headers.get("Content-Type")),
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=self._try_parse_body(
                        response.content, response.headers.get("Content-Type")
                    ),
                    duration_ms=duration_ms,
                )
                self.session.interactions.append(interaction)
                logger.info(f"Recorded: {method} {url} -> {response.status_code}")

            # Send response back to client
            self.send_response(response.status_code)
            for k, v in response.headers.items():
                if k.lower() not in ["transfer-encoding", "content-encoding"]:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            self.send_error(502, f"Proxy Error: {str(e)}")

    def _try_parse_body(self, body: Optional[bytes], content_type: Optional[str]) -> Any:
        if not body:
            return None
        if content_type and "application/json" in content_type:
            try:
                return json.loads(body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                pass
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            return str(body)  # Fallback to string representation


class RecordingProxy:
    """Proxy server that records interactions."""

    def __init__(self, port: int = 8090):
        """Initialize the proxy server."""
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.session: Optional[RecordedSession] = None

    def start(self, session_name: str):
        """Start the proxy server."""
        self.session = RecordedSession(name=session_name)
        RecordingProxyHandler.session = self.session

        self.server = HTTPServer(("localhost", self.port), RecordingProxyHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Recording Proxy started on port {self.port}")
        print(f"🔴 Recording Proxy active on http://localhost:{self.port}")
        print(f"Point your API tools to this proxy to record session '{session_name}'")

    def stop(self) -> RecordedSession:
        """Stop the proxy and return the session."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

        session = self.session
        self.session = None
        RecordingProxyHandler.session = None
        logger.info("Recording Proxy stopped")
        return session if session else RecordedSession(name="empty")
