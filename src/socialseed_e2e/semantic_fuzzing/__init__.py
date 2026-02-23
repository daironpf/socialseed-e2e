import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel


class LogicConstraint(BaseModel):
    field: str
    constraint_type: str
    description: str
    severity: str = "medium"


class FuzzingPayload(BaseModel):
    field: str
    value: Any
    rationale: str
    expected_behavior: str
    constraint: Optional[LogicConstraint] = None


class SemanticFuzzerConfig(BaseModel):
    openapi_spec: Optional[Path] = None
    max_payloads: int = 50
    use_llm: bool = True
    llm_model: str = "gpt-4"
    severity_filter: list[str] = ["critical", "high", "medium"]


class OpenAPIParser:
    def __init__(self, spec_path: Path):
        self.spec_path = spec_path
        self.spec = self._load_spec()

    def _load_spec(self) -> dict:
        with open(self.spec_path) as f:
            return json.load(f)

    def get_endpoints(self) -> list[dict]:
        endpoints = []
        paths = self.spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoints.append(
                        {
                            "path": path,
                            "method": method.upper(),
                            "parameters": details.get("parameters", []),
                            "requestBody": details.get("requestBody", {}),
                            "responses": details.get("responses", {}),
                        }
                    )
        return endpoints

    def get_schemas(self) -> dict:
        return self.spec.get("components", {}).get("schemas", {})


class ConstraintDetector:
    CONSTRAINT_PATTERNS = {
        "non_negative": {
            "pattern": r"(?i)(non-negative|positive|must.*be.*greater.*than.*0|minimum.*0)",
            "types": ["integer", "number", "float"],
        },
        "range_bound": {
            "pattern": r"(?i)(min|max|range|between|limit)",
            "types": ["integer", "number", "string"],
        },
        "required": {
            "pattern": r"(?i)(required|mandatory|must.*be.*present)",
            "types": ["string", "object", "array"],
        },
        "email_format": {
            "pattern": r"(?i)(email|e-mail)",
            "types": ["string"],
        },
        "url_format": {
            "pattern": r"(?i)(url|uri|endpoint)",
            "types": ["string"],
        },
        "length_bound": {
            "pattern": r"(?i)(minLength|maxLength|length|size)",
            "types": ["string", "array"],
        },
        "enum_constraint": {
            "pattern": r"(?i)(enum|one.*of|allowed.*values)",
            "types": ["string", "integer"],
        },
        "ownership": {
            "pattern": r"(?i)(owner|user.*cannot.*delete|authorization|permission)",
            "types": ["object"],
        },
    }

    def detect_constraints(
        self, schema: dict, field_name: str
    ) -> list[LogicConstraint]:
        constraints = []

        schema_json = json.dumps(schema).lower()

        for constraint_type, config in self.CONSTRAINT_PATTERNS.items():
            if re.search(config["pattern"], schema_json):
                description = self._extract_description(schema, constraint_type)
                constraints.append(
                    LogicConstraint(
                        field=field_name,
                        constraint_type=constraint_type,
                        description=description,
                        severity=self._determine_severity(constraint_type),
                    )
                )

        if "minimum" in schema:
            constraints.append(
                LogicConstraint(
                    field=field_name,
                    constraint_type="minimum_value",
                    description=f"Value must be >= {schema['minimum']}",
                    severity="high",
                )
            )

        if "maximum" in schema:
            constraints.append(
                LogicConstraint(
                    field=field_name,
                    constraint_type="maximum_value",
                    description=f"Value must be <= {schema['maximum']}",
                    severity="high",
                )
            )

        if "minLength" in schema:
            constraints.append(
                LogicConstraint(
                    field=field_name,
                    constraint_type="min_length",
                    description=f"Minimum length: {schema['minLength']}",
                    severity="medium",
                )
            )

        if "enum" in schema:
            constraints.append(
                LogicConstraint(
                    field=field_name,
                    constraint_type="enum_values",
                    description=f"Allowed values: {schema['enum']}",
                    severity="high",
                )
            )

        return constraints

    def _extract_description(self, schema: dict, constraint_type: str) -> str:
        if "description" in schema:
            return schema["description"]
        return f"Detected {constraint_type} constraint"

    def _determine_severity(self, constraint_type: str) -> str:
        severity_map = {
            "ownership": "critical",
            "non_negative": "high",
            "range_bound": "high",
            "required": "high",
            "enum_constraint": "high",
            "email_format": "medium",
            "url_format": "medium",
            "length_bound": "medium",
        }
        return severity_map.get(constraint_type, "medium")


class PayloadGenerator:
    def __init__(self, config: SemanticFuzzerConfig):
        self.config = config

    def generate_payloads(
        self,
        endpoint: dict,
        schema: dict,
        constraints: list[LogicConstraint],
    ) -> list[FuzzingPayload]:
        payloads = []

        for constraint in constraints:
            if constraint.severity not in self.config.severity_filter:
                continue

            generated = self._generate_for_constraint(endpoint, constraint, schema)
            payloads.extend(generated)

            if len(payloads) >= self.config.max_payloads:
                break

        return payloads[: self.config.max_payloads]

    def _generate_for_constraint(
        self,
        endpoint: dict,
        constraint: LogicConstraint,
        schema: dict,
    ) -> list[FuzzingPayload]:
        field = constraint.field
        ctype = constraint.constraint_type

        if ctype == "non_negative":
            return [
                FuzzingPayload(
                    field=field,
                    value=-1,
                    rationale="Testing negative value boundary",
                    expected_behavior="Should reject with 400 validation error",
                    constraint=constraint,
                ),
                FuzzingPayload(
                    field=field,
                    value=0,
                    rationale="Testing zero boundary",
                    expected_behavior="Should accept zero if non-negative",
                    constraint=constraint,
                ),
                FuzzingPayload(
                    field=field,
                    value=-999999,
                    rationale="Testing extreme negative value",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
            ]

        elif ctype == "minimum_value":
            min_val = schema.get("minimum", 0)
            return [
                FuzzingPayload(
                    field=field,
                    value=min_val - 1,
                    rationale=f"Testing just below minimum ({min_val})",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
                FuzzingPayload(
                    field=field,
                    value=min_val,
                    rationale=f"Testing exact minimum ({min_val})",
                    expected_behavior="Should accept",
                    constraint=constraint,
                ),
            ]

        elif ctype == "maximum_value":
            max_val = schema.get("maximum", 100)
            return [
                FuzzingPayload(
                    field=field,
                    value=max_val + 1,
                    rationale=f"Testing just above maximum ({max_val})",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
                FuzzingPayload(
                    field=field,
                    value=max_val + 999999,
                    rationale=f"Testing extreme above maximum ({max_val})",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
            ]

        elif ctype == "enum_values":
            enum_vals = schema.get("enum", [])
            return [
                FuzzingPayload(
                    field=field,
                    value="invalid_value_xyz",
                    rationale="Testing invalid enum value",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
            ]

        elif ctype == "email_format":
            return [
                FuzzingPayload(
                    field=field,
                    value="notanemail",
                    rationale="Testing invalid email format",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
                FuzzingPayload(
                    field=field,
                    value="@invalid.com",
                    rationale="Testing invalid email format",
                    expected_behavior="Should reject with 400",
                    constraint=constraint,
                ),
            ]

        elif ctype == "ownership":
            return [
                FuzzingPayload(
                    field=field,
                    value={"user_id": "other_user_id"},
                    rationale="Testing unauthorized access to another user's resource",
                    expected_behavior="Should reject with 403",
                    constraint=constraint,
                ),
            ]

        return []


class SemanticFuzzer:
    def __init__(
        self,
        config: SemanticFuzzerConfig,
        on_payload_generated: Optional[Callable[[FuzzingPayload], None]] = None,
    ):
        self.config = config
        self.on_payload_generated = on_payload_generated
        self.parser = (
            OpenAPIParser(config.openapi_spec) if config.openapi_spec else None
        )
        self.constraint_detector = ConstraintDetector()
        self.payload_generator = PayloadGenerator(config)
        self._payloads: list[FuzzingPayload] = []
        self._results: list[dict] = []

    def run(self) -> list[dict]:
        if not self.parser:
            raise ValueError("OpenAPI spec not configured")

        endpoints = self.parser.get_endpoints()
        schemas = self.parser.get_schemas()

        for endpoint in endpoints:
            self._fuzz_endpoint(endpoint, schemas)

        return self._results

    def _fuzz_endpoint(self, endpoint: dict, schemas: dict) -> None:
        method = endpoint["method"]
        path = endpoint["path"]

        request_body = endpoint.get("requestBody", {})
        if not request_body:
            return

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema_ref = json_content.get("schema", {})

        if "$ref" in schema_ref:
            ref_path = schema_ref["$ref"]
            schema_name = ref_path.split("/")[-1]
            full_schema = schemas.get(schema_name, {})
        else:
            full_schema = schema_ref

        self._analyze_and_fuzz(endpoint, full_schema)

    def _analyze_and_fuzz(self, endpoint: dict, schema: dict) -> None:
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            constraints = self.constraint_detector.detect_constraints(
                field_schema, field_name
            )

            if not constraints:
                continue

            payloads = self.payload_generator.generate_payloads(
                endpoint, field_schema, constraints
            )

            for payload in payloads:
                self._payloads.append(payload)

                if self.on_payload_generated:
                    self.on_payload_generated(payload)

                result = {
                    "endpoint": f"{endpoint['method']} {endpoint['path']}",
                    "field": payload.field,
                    "payload_value": payload.value,
                    "rationale": payload.rationale,
                    "expected_behavior": payload.expected_behavior,
                    "timestamp": datetime.now().isoformat(),
                }
                self._results.append(result)

    def get_payloads(self) -> list[FuzzingPayload]:
        return self._payloads

    def get_results(self) -> list[dict]:
        return self._results
