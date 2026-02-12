# Cloud Platform Integrations

socialseed-e2e provides native support for interacting with major cloud platforms during your E2E tests. This is useful for:
- Invoking Lambda/Cloud Functions to trigger background processes.
- Verifying logs in CloudWatch/Stackdriver.
- Managing cloud-native databases.
- Checking the health and status of containerized services (ECS, Cloud Run).

## AWS Integration

```python
from socialseed_e2e.cloud.aws import AWSProvider

aws = AWSProvider(region_name="us-east-1")

# Interacting with Lambda
lambda_fn = aws.get_lambda("my-processing-function")
result = lambda_fn.invoke({"orderId": "12345"})
print(f"Lambda result: {result}")

# Checking S3
bucket = aws.get_s3_bucket("my-app-uploads")
if bucket.exists("processed/order-12345.pdf"):
    print("File was successfully processed!")
```

## GCP Integration

```python
from socialseed_e2e.cloud.gcp import GCPProvider

gcp = GCPProvider(project_id="my-project")

# Interacting with Cloud Run
run_service = gcp.get_run_service("api-backend")
status = run_service.get_status()
print(f"Service status: {status}")
```

## Azure Integration

```python
from socialseed_e2e.cloud.azure import AzureProvider

azure = AzureProvider(subscription_id="your-subscription-id")

# Interaction with Container Instances
aci = azure.get_container_instance("my-rg", "worker-group")
aci.restart()
```

## Setup & Dependencies

To use these integrations, you need to install the corresponding cloud SDKs:

- **AWS**: `pip install boto3`
- **GCP**: `pip install google-cloud-functions google-cloud-run`
- **Azure**: `pip install azure-identity azure-mgmt-resource azure-mgmt-containerinstance`

The integrations are designed to fail gracefully with a descriptive error message if the libraries are missing.
