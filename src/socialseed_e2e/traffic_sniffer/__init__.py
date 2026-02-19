from pathlib import Path
from typing import Callable, Optional
import threading
from datetime import datetime

from pydantic import BaseModel


class CapturedRequest(BaseModel):
    method: str
    path: str
    headers: dict[str, str]
    request_body: Optional[str] = None
    timestamp: datetime


class CapturedResponse(BaseModel):
    status_code: int
    headers: dict[str, str]
    response_body: Optional[str] = None
    timestamp: datetime


class CapturedTraffic(BaseModel):
    request: CapturedRequest
    response: CapturedResponse
    duration_ms: float


class TrafficSnifferConfig(BaseModel):
    docker_network_id: Optional[str] = None
    target_port: int = 8080
    target_host: str = "localhost"
    output_file: Optional[Path] = None
    buffer_size: int = 100
    capture_mode: str = "reverse_proxy"


class TrafficSniffer:
    def __init__(
        self,
        config: TrafficSnifferConfig,
        on_traffic_captured: Optional[Callable[[CapturedTraffic], None]] = None,
    ):
        self.config = config
        self.on_traffic_captured = on_traffic_captured
        self._traffic_buffer: list[CapturedTraffic] = []
        self._running = False
        self._capture_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=5)

    def _capture_loop(self) -> None:
        if self.config.capture_mode == "reverse_proxy":
            self._run_reverse_proxy_mode()
        elif self.config.capture_mode == "docker_sidecar":
            self._run_docker_sidecar_mode()
        else:
            raise ValueError(f"Unknown capture mode: {self.config.capture_mode}")

    def _run_reverse_proxy_mode(self) -> None:
        try:
            from mitmproxy import http, options
            from mitmproxy.proxy.server import ProxyServer
            from mitmproxy.tools.dump import DumpMaster

            class TrafficAddon:
                def __init__(self, sniffer):
                    self.sniffer = sniffer

                def request(self, flow: http.HTTPFlow) -> None:
                    request = CapturedRequest(
                        method=flow.request.method,
                        path=flow.request.path,
                        headers=dict(flow.request.headers),
                        request_body=flow.request.content.decode("utf-8")
                        if flow.request.content
                        else None,
                        timestamp=datetime.now(),
                    )
                    flow.metadata["_sniffer_request"] = request

                def response(self, flow: http.HTTPFlow) -> None:
                    request_data: Optional[CapturedRequest] = flow.metadata.get(
                        "_sniffer_request"
                    )
                    if not request_data:
                        return

                    response = CapturedResponse(
                        status_code=flow.response.status_code,
                        headers=dict(flow.response.headers),
                        response_body=flow.response.content.decode("utf-8")
                        if flow.response.content
                        else None,
                        timestamp=datetime.now(),
                    )

                    duration = (
                        response.timestamp - request_data.timestamp
                    ).total_seconds() * 1000

                    traffic = CapturedTraffic(
                        request=request_data,
                        response=response,
                        duration_ms=duration,
                    )

                    self.sniffer._add_traffic(traffic)

            opts = options.Options(
                listen_host=self.config.target_host,
                listen_port=self.config.target_port + 1,
                mode=f"regular@{self.config.target_port}",
            )
            server = ProxyServer(opts)
            addons = [TrafficAddon(self)]

            m = DumpMaster(opts)
            m.addons.add(*addons)

            try:
                m.run()
            except KeyboardInterrupt:
                pass
        except ImportError:
            self._run_simple_http_proxy()

    def _run_simple_http_proxy(self) -> None:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class ProxyHandler(BaseHTTPRequestHandler):
            sniffer: "TrafficSniffer" = None

            def _handle_request(self, method: str) -> None:
                content_length = int(self.headers.get("Content-Length", 0))
                request_body = (
                    self.rfile.read(content_length).decode("utf-8")
                    if content_length > 0
                    else None
                )

                request = CapturedRequest(
                    method=method,
                    path=self.path,
                    headers=dict(self.headers),
                    request_body=request_body,
                    timestamp=datetime.now(),
                )

                from urllib.request import urlopen, Request

                target_url = f"http://{self.sniffer.config.target_host}:{self.sniffer.config.target_port}{self.path}"
                req = Request(
                    target_url,
                    data=request_body.encode("utf-8") if request_body else None,
                    headers=dict(self.headers),
                    method=method,
                )

                try:
                    response = urlopen(req, timeout=30)
                    response_body = response.read().decode("utf-8")
                    status_code = response.getcode()
                    response_headers = dict(response.headers)
                except Exception as e:
                    response_body = str(e)
                    status_code = 502
                    response_headers = {}

                response = CapturedResponse(
                    status_code=status_code,
                    headers=response_headers,
                    response_body=response_body,
                    timestamp=datetime.now(),
                )

                duration = (
                    response.timestamp - request.timestamp
                ).total_seconds() * 1000

                traffic = CapturedTraffic(
                    request=request,
                    response=response,
                    duration_ms=duration,
                )

                self.sniffer._add_traffic(traffic)

                self.send_response(status_code)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response_body.encode("utf-8"))

            def do_GET(self) -> None:
                self._handle_request("GET")

            def do_POST(self) -> None:
                self._handle_request("POST")

            def do_PUT(self) -> None:
                self._handle_request("PUT")

            def do_DELETE(self) -> None:
                self._handle_request("DELETE")

            def do_PATCH(self) -> None:
                self._handle_request("PATCH")

            def log_message(self, format, *args) -> None:
                pass

        ProxyHandler.sniffer = self

        server = HTTPServer(
            (self.config.target_host, self.config.target_port + 1), ProxyHandler
        )
        server.serve_forever()

    def _run_docker_sidecar_mode(self) -> None:
        self._run_pcap_capture()

    def _run_pcap_capture(self) -> None:
        try:
            from scapy.all import sniff, TCP, Raw
        except ImportError:
            raise ImportError(
                "scapy is required for docker sidecar mode. Install with: pip install scapy"
            )

        filter_str = f"tcp and port {self.config.target_port}"

        def packet_handler(pkt):
            if TCP in pkt and Raw in pkt:
                try:
                    data = pkt[Raw].load.decode("utf-8", errors="ignore")
                    if "HTTP" in data:
                        self._parse_http_packet(pkt, data)
                except Exception:
                    pass

        sniff(filter=filter_str, prn=packet_handler, store=0)

    def _parse_http_packet(self, pkt, data: str) -> None:
        lines = data.split("\r\n")
        if not lines:
            return

        request_line = lines[0].split()
        if len(request_line) < 2:
            return

        method = request_line[0]
        path = request_line[1] if len(request_line) > 1 else "/"

        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        body_idx = data.find("\r\n\r\n")
        request_body = data[body_idx + 4 :] if body_idx > 0 else None

        request = CapturedRequest(
            method=method,
            path=path,
            headers=headers,
            request_body=request_body,
            timestamp=datetime.now(),
        )

        response = CapturedResponse(
            status_code=0,
            headers={},
            response_body=None,
            timestamp=datetime.now(),
        )

        traffic = CapturedTraffic(
            request=request,
            response=response,
            duration_ms=0,
        )

        self._add_traffic(traffic)

    def _add_traffic(self, traffic: CapturedTraffic) -> None:
        self._traffic_buffer.append(traffic)
        if len(self._traffic_buffer) > self.config.buffer_size:
            self._traffic_buffer.pop(0)

        if self.on_traffic_captured:
            self.on_traffic_captured(traffic)

        if self.config.output_file:
            self._save_to_file(traffic)

    def _save_to_file(self, traffic: CapturedTraffic) -> None:
        output_path = self.config.output_file
        if output_path:
            with open(output_path, "a") as f:
                f.write(traffic.model_dump_json() + "\n")

    def get_traffic(self) -> list[CapturedTraffic]:
        return self._traffic_buffer.copy()

    def clear_buffer(self) -> None:
        self._traffic_buffer.clear()
