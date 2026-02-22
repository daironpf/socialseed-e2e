"""
Semantic Fuzzing Engine for Shadow Runner.

This module provides intelligent mutation capabilities that understand
the schema and semantics of API payloads to generate meaningful test cases.

Features:
- AI-powered semantic understanding of payload structure
- Type-aware mutations (strings, numbers, dates, UUIDs, etc.)
- Security-focused mutation patterns (SQL injection, XSS, etc.)
- Context-aware mutations based on field meaning
"""

import json
import random
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.shadow_runner.models import (
    CapturedRequest,
    FuzzingConfig,
    FuzzingStrategy,
    MutatedRequest,
    MutationType,
    SemanticMutation,
)


class SemanticFuzzer:
    """
    AI-powered semantic fuzzing engine that understands payload structure
    and generates intelligent mutations.
    """

    def __init__(self, config: FuzzingConfig):
        self.config = config
        self.mutation_strategies = self._build_mutation_strategies()
        self.field_classifiers = self._build_field_classifiers()

    def _build_mutation_strategies(self) -> Dict[MutationType, Callable]:
        """Build mapping of mutation types to their implementation."""
        return {
            MutationType.STRING_BOUNDARY: self._mutate_string_boundary,
            MutationType.NUMBER_BOUNDARY: self._mutate_number_boundary,
            MutationType.INJECT_SQL: self._inject_sql,
            MutationType.INJECT_XSS: self._inject_xss,
            MutationType.INJECT_PATH_TRAVERSAL: self._inject_path_traversal,
            MutationType.INJECT_COMMAND: self._inject_command,
            MutationType.NULL_INJECTION: self._mutate_null,
            MutationType.TYPE_MISMATCH: self._mutate_type,
            MutationType.ENUM_EXHAUSTION: self._mutate_enum,
            MutationType.LENGTH_EXTREME: self._mutate_length,
            MutationType.UNICODE_FUZZING: self._mutate_unicode,
            MutationType.JSON_STRUCTURE: self._mutate_json_structure,
            MutationType.HEADER_INJECTION: self._mutate_header,
            MutationType.SCHEMA_VIOLATION: self._mutate_schema,
        }

    def _build_field_classifiers(self) -> Dict[str, Callable]:
        """Build classifiers to understand field semantics."""
        return {
            "email": self._classify_email,
            "password": self._classify_password,
            "username": self._classify_username,
            "phone": self._classify_phone,
            "date": self._classify_date,
            "datetime": self._classify_datetime,
            "uuid": self._classify_uuid,
            "id": self._classify_id,
            "url": self._classify_url,
            "price": self._classify_price,
            "count": self._classify_count,
            "boolean": self._classify_boolean,
        }

    def fuzz_request(self, request: CapturedRequest) -> List[MutatedRequest]:
        """Generate fuzzed variations of a captured request."""
        mutations: List[MutatedRequest] = []
        mutation_types = self._get_mutation_types()

        num_mutations = min(
            self.config.mutations_per_request,
            len(mutation_types) * len(self._get_mutable_fields(request)),
        )

        for _ in range(num_mutations):
            mutation_type = random.choice(mutation_types)
            mutable_fields = self._get_mutable_fields(request)

            if not mutable_fields:
                continue

            field = random.choice(list(mutable_fields.keys()))
            original_value = mutable_fields[field]

            if mutation_type in self.mutation_strategies:
                mutated_value = self.mutation_strategies[mutation_type](
                    field, original_value, mutable_fields
                )

                if mutated_value is not None and mutated_value != original_value:
                    mutation = MutatedRequest(
                        original_request=request,
                        mutation_type=mutation_type,
                        mutated_field=field,
                        original_value=original_value,
                        mutated_value=mutated_value,
                        fuzzing_strategy=self.config.strategy,
                    )
                    mutations.append(mutation)

        return mutations

    def _get_mutation_types(self) -> List[MutationType]:
        """Get list of mutation types to apply."""
        if self.config.include_mutation_types:
            return self.config.include_mutation_types

        excluded = set(self.config.exclude_mutation_types or [])
        all_types = set(MutationType)
        return [t for t in all_types if t not in excluded]

    def _get_mutable_fields(self, request: CapturedRequest) -> Dict[str, Any]:
        """Extract fields that can be mutated from request."""
        fields = {}

        if request.query_params:
            fields.update(request.query_params)

        if request.body:
            fields.update(self._flatten_dict(request.body))

        if request.form_data:
            fields.update(request.form_data)

        return fields

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary for mutation."""
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key))
            elif isinstance(v, list):
                items[new_key] = json.dumps(v)
            else:
                items[new_key] = v
        return items

    def _classify_field(self, field_name: str, value: Any) -> str:
        """Classify field type based on name and value."""
        field_lower = field_name.lower()

        for classifier_name, classifier in self.field_classifiers.items():
            if classifier_name in field_lower:
                return classifier_name

        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "count"
        elif isinstance(value, float):
            return "price"
        elif isinstance(value, str):
            if re.match(r"^[\d\-:T.Z]+$", value):
                return "datetime"
            elif re.match(r"^[\w\-]+@[\w\-]+\.[\w\-]+$", value):
                return "email"
            elif re.match(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                value,
                re.I,
            ):
                return "uuid"
            elif re.match(r"^\d+$", value):
                return "count"

        return "unknown"

    def _mutate_string_boundary(self, field: str, value: Any, context: Dict) -> Any:
        """Mutate string at boundary values."""
        if not isinstance(value, str):
            return value

        mutations = [
            "",
            "a" * 1,
            "a" * 255,
            "a" * 256,
            "a" * 1000,
            "a" * 10000,
            " ",
            "\t",
            "\n",
            "\r",
            "\x00",
            "\\",
            random.choice(["", "A" * 1000, "áéíóú", "🎉"]),
        ]
        return random.choice(mutations)

    def _mutate_number_boundary(self, field: str, value: Any, context: Dict) -> Any:
        """Mutate numbers at boundary values."""
        if isinstance(value, (int, float)):
            return random.choice(
                [
                    0,
                    -1,
                    1,
                    127,
                    128,
                    255,
                    256,
                    32767,
                    32768,
                    65535,
                    65536,
                    2147483647,
                    2147483648,
                    999999999999,
                    -999999999999,
                    0.0,
                    -0.0,
                    float("inf"),
                    float("-inf"),
                    float("nan"),
                ]
            )
        elif isinstance(value, str) and value.isdigit():
            return random.choice(["0", "-1", "999999999999", "abc"])
        return value

    def _inject_sql(self, field: str, value: Any, context: Dict) -> Any:
        """Inject SQL injection patterns."""
        sql_payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "'; DROP TABLE users; --",
            "1' AND '1'='1",
            "1 UNION SELECT NULL--",
            "1 UNION SELECT NULL, NULL--",
            "admin'--",
            "admin' #",
            "' OR ''='",
            "1' ORDER BY 1--",
            "1' ORDER BY 10--",
            "1' SLEEP(5)--",
            "1'; WAITFOR DELAY '00:00:05'--",
        ]
        return random.choice(sql_payloads)

    def _inject_xss(self, field: str, value: Any, context: Dict) -> Any:
        """Inject XSS patterns."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<body onload=alert('XSS')>",
            "<iframe src='javascript:alert(`XSS`)'",
            "<script>console.log('XSS')</script>",
            "\"><script>alert('XSS')</script>",
            "'-alert('XSS')-'",
            "<script>eval(atob('YWxlcnQoJ1hTUycp'))</script>",
        ]
        return random.choice(xss_payloads)

    def _inject_path_traversal(self, field: str, value: Any, context: Dict) -> Any:
        """Inject path traversal patterns."""
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....\/....\/....\/etc\/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]
        return random.choice(path_payloads)

    def _inject_command(self, field: str, value: Any, context: Dict) -> Any:
        """Inject command injection patterns."""
        cmd_payloads = [
            "; ls -la",
            "| ls -la",
            "`ls -la`",
            "$(ls -la)",
            "\nls -la\n",
            "; cat /etc/passwd",
            "| whoami",
            "& whoami",
            "&& whoami",
            "|| whoami",
        ]
        return random.choice(cmd_payloads)

    def _mutate_null(self, field: str, value: Any, context: Dict) -> Any:
        """Inject null values."""
        return random.choice([None, "null", "NULL", "Null", "undefined", "NaN", ""])

    def _mutate_type(self, field: str, value: Any, context: Dict) -> Any:
        """Introduce type mismatches."""
        if isinstance(value, str):
            return random.choice(
                ["123", "true", "false", "[1,2,3]", '{"key": "value"}', ""]
            )
        elif isinstance(value, int):
            return random.choice(["string", "true", "12.34", '{"num": 1}'])
        elif isinstance(value, bool):
            return random.choice(["true", "false", "1", "0", "yes", "no", ""])
        return value

    def _mutate_enum(self, field: str, value: Any, context: Dict) -> Any:
        """Exhaust enum values."""
        return random.choice(["unknown", "INVALID", "_INVALID", "null", value])

    def _mutate_length(self, field: str, value: Any, context: Dict) -> Any:
        """Generate extreme length values."""
        if isinstance(value, str):
            lengths = [1, 10, 100, 1000, 10000, 100000]
            length = random.choice(lengths)
            return "a" * length
        return value

    def _mutate_unicode(self, field: str, value: Any, context: Dict) -> Any:
        """Fuzz with Unicode characters."""
        unicode_payloads = [
            "Café",
            "日本語",
            "Русский",
            "العربية",
            "😀",
            "\u0000",
            "\uffff",
            "‍️",
            "Ḽ̷̩̋",
            "O̷̜͐",
        ]
        return random.choice(unicode_payloads)

    def _mutate_json_structure(self, field: str, value: Any, context: Dict) -> Any:
        """Mutate JSON structure."""
        return random.choice(
            [
                {"key": "value"},
                [],
                [1, 2, 3],
                "string",
                123,
                True,
                False,
                None,
                {},
                {"nested": {"deep": value}},
            ]
        )

    def _mutate_header(self, field: str, value: Any, context: Dict) -> Any:
        """Mutate HTTP headers."""
        header_payloads = [
            "Basic dXNlcjpwYXNz",
            "Bearer invalid_token",
            "Token",
            "<script>alert(1)</script>",
            "\r\nContent-Length: 0\r\n",
            "X-Forwarded-For: 127.0.0.1",
        ]
        return random.choice(header_payloads)

    def _mutate_schema(self, field: str, value: Any, context: Dict) -> Any:
        """Violate expected schema."""
        return random.choice(
            [
                {"unexpected": "structure"},
                ["array", "instead", "of", "object"],
                "string_instead_of_number",
                123,
                True,
                None,
            ]
        )

    def _classify_email(self, field: str, value: Any) -> str:
        return "email"

    def _classify_password(self, field: str, value: Any) -> str:
        return "password"

    def _classify_username(self, field: str, value: Any) -> str:
        return "username"

    def _classify_phone(self, field: str, value: Any) -> str:
        return "phone"

    def _classify_date(self, field: str, value: Any) -> str:
        return "date"

    def _classify_datetime(self, field: str, value: Any) -> str:
        return "datetime"

    def _classify_uuid(self, field: str, value: Any) -> str:
        return "uuid"

    def _classify_id(self, field: str, value: Any) -> str:
        return "id"

    def _classify_url(self, field: str, value: Any) -> str:
        return "url"

    def _classify_price(self, field: str, value: Any) -> str:
        return "price"

    def _classify_count(self, field: str, value: Any) -> str:
        return "count"

    def _classify_boolean(self, field: str, value: Any) -> str:
        return "boolean"


class IntelligentFuzzer(SemanticFuzzer):
    """
    AI-powered fuzzer that uses semantic understanding to generate
    more meaningful mutations based on field context.
    """

    def __init__(self, config: FuzzingConfig, ai_model: Optional[str] = None):
        super().__init__(config)
        self.ai_model = ai_model

    def generate_smart_mutations(
        self, request: CapturedRequest
    ) -> List[SemanticMutation]:
        """Generate intelligent semantic mutations using AI understanding."""
        mutations = []
        mutable_fields = self._get_mutable_fields(request)

        for field, value in mutable_fields.items():
            field_type = self._classify_field(field, value)

            mutation = self._generate_semantic_mutation(
                request.id, field, value, field_type
            )
            if mutation:
                mutations.append(mutation)

        return mutations

    def _generate_semantic_mutation(
        self, request_id: str, field: str, value: Any, field_type: str
    ) -> Optional[SemanticMutation]:
        """Generate a semantically meaningful mutation."""
        mutation_id = str(uuid.uuid4())

        if field_type == "email":
            return SemanticMutation(
                mutation_id=mutation_id,
                request_id=request_id,
                field_path=field,
                original_value=value,
                mutated_value="test@invalid\x00domain.com",
                mutation_reason="Test email injection",
                expected_impact="Validate email validation",
            )
        elif field_type == "password":
            return SemanticMutation(
                mutation_id=mutation_id,
                request_id=request_id,
                field_path=field,
                original_value=value,
                mutated_value="",
                mutation_reason="Empty password test",
                expected_impact="Verify password requirements",
            )
        elif field_type == "date":
            return SemanticMutation(
                mutation_id=mutation_id,
                request_id=request_id,
                field_path=field,
                original_value=value,
                mutated_value="1900-01-01",
                mutation_reason="Edge case date",
                expected_impact="Verify date validation",
            )

        return None


__all__ = ["SemanticFuzzer", "IntelligentFuzzer"]
