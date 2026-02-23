"""Azure integration for socialseed-e2e."""

from typing import Any, Dict, List, Optional

from socialseed_e2e.cloud import CloudFunction, CloudProvider, CloudService

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureProvider(CloudProvider):
    """Azure Cloud Provider implementation."""

    def __init__(self, subscription_id: str):
        if not AZURE_AVAILABLE:
            raise ImportError("Azure libraries are required. Install them with 'pip install azure-identity azure-mgmt-resource azure-mgmt-containerinstance'")

        self.subscription_id = subscription_id
        self.credentials = DefaultAzureCredential()

    def health_check(self) -> bool:
        """Verify Azure connection."""
        try:
            client = ResourceManagementClient(self.credentials, self.subscription_id)
            client.providers.list()
            return True
        except Exception:
            return False

    def get_function(self, resource_group: str, app_name: str, function_name: str) -> 'AzureFunction':
        return AzureFunction(resource_group, app_name, function_name)

    def get_container_instance(self, resource_group: str, container_group_name: str) -> 'AzureContainerInstance':
        return AzureContainerInstance(self.credentials, self.subscription_id, resource_group, container_group_name)


class AzureFunction(CloudFunction):
    """Azure Functions implementation."""

    def __init__(self, resource_group: str, app_name: str, function_name: str):
        self.resource_group = resource_group
        self.app_name = app_name
        self.function_name = function_name

    def invoke(self, payload: Dict[str, Any]) -> Any:
        # Azure Functions are primarily invoked via HTTP
        return {"status": "invoked", "app": self.app_name, "function": self.function_name}

    def get_logs(self, limit: int = 10) -> List[str]:
        # Logs usually come from App Insights or Log Analytics
        return ["Log retrieval from App Insights not implemented yet"]


class AzureContainerInstance(CloudService):
    """Azure Container Instance implementation."""

    def __init__(self, credentials, subscription_id: str, resource_group: str, group_name: str):
        self.client = ContainerInstanceManagementClient(credentials, subscription_id)
        self.resource_group = resource_group
        self.group_name = group_name

    def get_status(self) -> str:
        group = self.client.container_groups.get(self.resource_group, self.group_name)
        return group.instance_view.state

    def restart(self) -> bool:
        self.client.container_groups.begin_start(self.resource_group, self.group_name)
        return True
