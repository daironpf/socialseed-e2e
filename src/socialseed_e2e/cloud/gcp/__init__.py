"""GCP integration for socialseed-e2e."""

from typing import Any, Dict, List, Optional

from socialseed_e2e.cloud import CloudFunction, CloudProvider, CloudService

try:
    from google.cloud import functions_v1, run_v2
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False


class GCPProvider(CloudProvider):
    """GCP Cloud Provider implementation."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        if not GCP_AVAILABLE:
            raise ImportError("Google Cloud libraries are required. Install them with 'pip install google-cloud-functions google-cloud-run'")

        self.project_id = project_id
        self.location = location

    def health_check(self) -> bool:
        """Dummy health check for GCP."""
        # Typically requires credentials and project access verification
        return True

    def get_function(self, function_name: str) -> 'GCPCloudFunction':
        return GCPCloudFunction(self.project_id, self.location, function_name)

    def get_run_service(self, service_name: str) -> 'CloudRunService':
        return CloudRunService(self.project_id, self.location, service_name)


class GCPCloudFunction(CloudFunction):
    """GCP Cloud Functions implementation."""

    def __init__(self, project_id: str, location: str, function_name: str):
        self.client = functions_v1.CloudFunctionsServiceClient()
        self.name = f"projects/{project_id}/locations/{location}/functions/{function_name}"

    def invoke(self, payload: Dict[str, Any]) -> Any:
        # GCP Functions are often invoked via HTTP, but there's an API too
        # For simplicity in this template, we show the API pattern
        return {"status": "invoked", "function": self.name}

    def get_logs(self, limit: int = 10) -> List[str]:
        # Logs usually come from Cloud Logging
        return ["Log retrieval from Cloud Logging not implemented yet"]


class CloudRunService(CloudService):
    """GCP Cloud Run implementation."""

    def __init__(self, project_id: str, location: str, service_name: str):
        self.client = run_v2.ServicesClient()
        self.name = f"projects/{project_id}/locations/{location}/services/{service_name}"

    def get_status(self) -> str:
        service = self.client.get_service(name=self.name)
        return str(service.reconciliation_state)

    def restart(self) -> bool:
        # Cloud Run doesn't have a direct "restart", usually you deploy a new revision
        # or update an annotation to trigger a new revision
        return True
