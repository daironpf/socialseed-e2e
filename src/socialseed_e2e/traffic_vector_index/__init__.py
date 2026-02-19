from pathlib import Path
from typing import Any, Callable, Optional
import hashlib
import json
import re
import threading
from datetime import datetime

from pydantic import BaseModel

from ..traffic_sniffer import CapturedTraffic


class VectorEntry(BaseModel):
    id: str
    traffic_id: str
    method: str
    path: str
    timestamp: datetime
    embedding: list[float]
    raw_text: str


class TrafficVectorConfig(BaseModel):
    vector_db_path: Path = Path(".e2e/vector_store")
    embedding_model: str = "text-embedding-3-small"
    use_local: bool = False
    local_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    pi_masking_enabled: bool = True


class PIIMasker:
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")
    API_KEY_PATTERN = re.compile(
        r"(?i)(api[_-]?key|token|secret|password)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{16,})"
    )
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-csrf-token",
        "proxy-authorization",
    }

    def mask(self, text: str) -> str:
        text = self.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
        text = self.PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
        text = self.CREDIT_CARD_PATTERN.sub("[CREDIT_CARD_REDACTED]", text)
        text = self.API_KEY_PATTERN.sub(r"\1=[REDACTED]", text)
        text = self.SSN_PATTERN.sub("[SSN_REDACTED]", text)
        return text

    def mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        masked = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                masked[key] = "[REDACTED]"
            else:
                masked[key] = value
        return masked


class EmbeddingGenerator:
    def __init__(self, config: TrafficVectorConfig):
        self.config = config
        self._model = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        if self.config.use_local:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.config.local_model)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. Install with: pip install sentence-transformers"
                )
        else:
            try:
                import openai

                self._client = openai.OpenAI()
            except ImportError:
                raise ImportError(
                    "openai is required for OpenAI embeddings. Install with: pip install openai"
                )

    def generate(self, text: str) -> list[float]:
        if self._model:
            embedding = self._model.encode(text)
            return embedding.tolist()
        else:
            response = self._client.embeddings.create(
                model=self.config.embedding_model,
                input=text,
            )
            return response.data[0].embedding


class TrafficVectorIndexer:
    def __init__(
        self,
        config: TrafficVectorConfig,
        on_indexed: Optional[Callable[[VectorEntry], None]] = None,
    ):
        self.config = config
        self.on_indexed = on_indexed
        self.masker = PIIMasker()
        self.embedder = EmbeddingGenerator(config)
        self._entries: list[VectorEntry] = []
        self._lock = threading.Lock()
        self._processing = False
        self._traffic_queue: list[CapturedTraffic] = []
        self._worker_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._processing = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        self._processing = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

    def add_traffic(self, traffic: CapturedTraffic) -> None:
        with self._lock:
            self._traffic_queue.append(traffic)

    def _process_queue(self) -> None:
        while self._processing:
            traffic = None
            with self._lock:
                if self._traffic_queue:
                    traffic = self._traffic_queue.pop(0)

            if traffic:
                self._index_traffic(traffic)
            else:
                import time

                time.sleep(0.1)

    def _index_traffic(self, traffic: CapturedTraffic) -> None:
        request = traffic.request
        response = traffic.response

        traffic_id = hashlib.sha256(
            f"{request.method}{request.path}{request.timestamp.isoformat()}".encode()
        ).hexdigest()[:16]

        raw_text = self._build_searchable_text(traffic)

        if self.config.pi_masking_enabled:
            raw_text = self.masker.mask(raw_text)

        try:
            embedding = self.embedder.generate(raw_text)
        except Exception as e:
            import logging

            logging.warning(f"Failed to generate embedding: {e}")
            return

        entry = VectorEntry(
            id=traffic_id,
            traffic_id=traffic_id,
            method=request.method,
            path=request.path,
            timestamp=request.timestamp,
            embedding=embedding,
            raw_text=raw_text[:500],
        )

        with self._lock:
            self._entries.append(entry)

        if self.on_indexed:
            self.on_indexed(entry)

        self._save_entry(entry)

    def _build_searchable_text(self, traffic: CapturedTraffic) -> str:
        parts = [
            f"Method: {traffic.request.method}",
            f"Path: {traffic.request.path}",
            f"Status: {traffic.response.status_code}",
        ]

        if traffic.request.headers:
            non_sensitive = self.masker.mask_headers(traffic.request.headers)
            parts.append(f"Headers: {json.dumps(non_sensitive)}")

        if traffic.request.request_body:
            parts.append(f"Request Body: {traffic.request.request_body[:200]}")

        if traffic.response.response_body:
            parts.append(f"Response Body: {traffic.response.response_body[:200]}")

        return " | ".join(parts)

    def _save_entry(self, entry: VectorEntry) -> None:
        self.config.vector_db_path.mkdir(parents=True, exist_ok=True)
        index_file = self.config.vector_db_path / "index.jsonl"
        with open(index_file, "a") as f:
            f.write(entry.model_dump_json() + "\n")

    def search(self, query: str, top_k: int = 5) -> list[VectorEntry]:
        query_embedding = self.embedder.generate(query)

        results = []
        for entry in self._entries:
            similarity = self._cosine_similarity(query_embedding, entry.embedding)
            results.append((entry, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:top_k]]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)

    def get_all_entries(self) -> list[VectorEntry]:
        with self._lock:
            return self._entries.copy()
