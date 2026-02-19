from pathlib import Path
from typing import Any, Callable, Optional
import hashlib
import re
from enum import Enum

from pydantic import BaseModel


class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    API_KEY = "api_key"
    PASSWORD = "password"
    ADDRESS = "address"
    NAME = "name"
    IP_ADDRESS = "ip_address"


class MaskingRule(BaseModel):
    pii_type: PIIType
    pattern: str
    replacement: str
    enabled: bool = True


class MaskedValue(BaseModel):
    original: str
    masked: str
    pii_type: PIIType
    confidence: float


class PIIMaskingConfig(BaseModel):
    enabled: bool = True
    strict_mode: bool = False
    preserve_format: bool = True
    hash_salt: Optional[str] = None
    custom_rules: list[MaskingRule] = []


class RegexMasker:
    DEFAULT_RULES = [
        MaskingRule(
            pii_type=PIIType.EMAIL,
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            replacement="[EMAIL_REDACTED]",
        ),
        MaskingRule(
            pii_type=PIIType.PHONE,
            pattern=r"\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b",
            replacement="[PHONE_REDACTED]",
        ),
        MaskingRule(
            pii_type=PIIType.CREDIT_CARD,
            pattern=r"\b(?:\d{4}[- ]?){3}\d{4}\b",
            replacement="[CREDIT_CARD_REDACTED]",
        ),
        MaskingRule(
            pii_type=PIIType.SSN,
            pattern=r"\b\d{3}-\d{2}-\d{4}\b",
            replacement="[SSN_REDACTED]",
        ),
        MaskingRule(
            pii_type=PIIType.API_KEY,
            pattern=r"(?i)(?:api[_-]?key|api[_-]?token|access[_-]?token|secret[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{16,})['\"]?",
            replacement="API_KEY=[REDACTED]",
        ),
        MaskingRule(
            pii_type=PIIType.PASSWORD,
            pattern=r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"\s]{4,})['\"]?",
            replacement="password=[REDACTED]",
        ),
        MaskingRule(
            pii_type=PIIType.IP_ADDRESS,
            pattern=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            replacement="[IP_REDACTED]",
        ),
    ]

    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-csrf-token",
        "x-session-id",
        "proxy-authorization",
        "www-authenticate",
    }

    def __init__(self, config: PIIMaskingConfig):
        self.config = config
        self.rules = self.DEFAULT_RULES + config.custom_rules
        self._compile_patterns()

    def _compile_patterns(self):
        for rule in self.rules:
            if not hasattr(rule, "_compiled"):
                rule._compiled = re.compile(rule.pattern)

    def mask_text(self, text: str) -> tuple[str, list[MaskedValue]]:
        if not self.config.enabled:
            return text, []

        masked_values = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            matches = rule._compiled.finditer(text)
            for match in matches:
                original = match.group()
                masked = rule.replacement

                if self.config.preserve_format:
                    if rule.pii_type == PIIType.CREDIT_CARD:
                        masked = f"[CARD:{original[:4]}****{original[-4:]}]"
                    elif rule.pii_type == PIIType.EMAIL:
                        parts = original.split("@")
                        if len(parts) == 2:
                            masked = f"{parts[0][:2]}***@{parts[1]}"

                masked_values.append(
                    MaskedValue(
                        original=original,
                        masked=masked,
                        pii_type=rule.pii_type,
                        confidence=0.95,
                    )
                )

                text = text.replace(original, masked)

        return text, masked_values

    def mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        masked = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                if self.config.hash_salt:
                    value = hashlib.sha256(
                        f"{self.config.hash_salt}{value}".encode()
                    ).hexdigest()[:16]
                else:
                    value = "[REDACTED]"
            masked[key] = value
        return masked

    def mask_json(self, data: dict) -> tuple[dict, list[MaskedValue]]:
        all_masked = []

        def recursive_mask(obj):
            if isinstance(obj, str):
                masked, vals = self.mask_text(obj)
                all_masked.extend(vals)
                return masked
            elif isinstance(obj, dict):
                return {k: recursive_mask(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recursive_mask(item) for item in obj]
            else:
                return obj

        masked_data = recursive_mask(data)
        return masked_data, all_masked

    def mask_request_body(self, body: Any) -> tuple[Any, list[MaskedValue]]:
        if isinstance(body, str):
            return self.mask_text(body)
        elif isinstance(body, dict):
            return self.mask_json(body)
        elif isinstance(body, bytes):
            try:
                text = body.decode("utf-8")
                masked_text, vals = self.mask_text(text)
                return masked_text.encode("utf-8"), vals
            except UnicodeDecodeError:
                return body, []
        return body, []


class PresidioMasker:
    def __init__(self, config: PIIMaskingConfig):
        self.config = config
        self.regex_masker = RegexMasker(config)
        self._presidio_available = False

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self._presidio_available = True
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
        except ImportError:
            pass

    def analyze(self, text: str) -> list[dict]:
        if not self._presidio_available:
            return []

        results = self.analyzer.analyze(text)
        return [
            {
                "entity_type": r.entity_type,
                "text": r.text,
                "start": r.start,
                "end": r.end,
                "score": r.score,
            }
            for r in results
        ]

    def anonymize(self, text: str) -> tuple[str, list[dict]]:
        if not self._presidio_available:
            return self.regex_masker.mask_text(text)

        analyzed = self.analyze(text)

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzed,
        )

        return anonymized.text, analyzed


class PIIMaskingService:
    def __init__(
        self,
        config: PIIMaskingConfig,
        on_pii_detected: Optional[Callable[[list[MaskedValue]], None]] = None,
    ):
        self.config = config
        self.on_pii_detected = on_pii_detected
        self.regex_masker = RegexMasker(config)
        self.presidio = PresidioMasker(config)
        self._stats = {
            "total_requests": 0,
            "pii_detected": 0,
            "pii_by_type": {pt.value: 0 for pt in PIIType},
        }

    def mask_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: Any = None,
    ) -> tuple[dict, Any, list[MaskedValue]]:
        self._stats["total_requests"] += 1

        masked_headers = self.regex_masker.mask_headers(headers)

        masked_body = body
        body_pii = []
        if body:
            masked_body, body_pii = self.regex_masker.mask_request_body(body)

        all_pii = body_pii

        if self.on_pii_detected and all_pii:
            self.on_pii_detected(all_pii)

        if all_pii:
            self._stats["pii_detected"] += 1
            for pv in all_pii:
                self._stats["pii_by_type"][pv.pii_type.value] += 1

        return masked_headers, masked_body, all_pii

    def mask_response(
        self,
        status_code: int,
        headers: dict[str, str],
        body: Any = None,
    ) -> tuple[dict, Any, list[MaskedValue]]:
        masked_headers = self.regex_masker.mask_headers(headers)

        masked_body = body
        body_pii = []
        if body:
            masked_body, body_pii = self.regex_masker.mask_request_body(body)

        return masked_headers, masked_body, body_pii

    def get_stats(self) -> dict:
        return self._stats.copy()
