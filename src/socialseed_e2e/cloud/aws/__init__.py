"""AWS integration for socialseed-e2e."""

import json
from typing import Any, Dict, List, Optional
from socialseed_e2e.cloud import CloudProvider, CloudFunction, CloudService, CloudDatabase

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSProvider(CloudProvider):
    """AWS Cloud Provider implementation."""

    def __init__(self, region_name: str = "us-east-1", profile_name: Optional[str] = None):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for AWS integration. Install it with 'pip install boto3'")
        
        self.session = boto3.Session(region_name=region_name, profile_name=profile_name)
        self.region = region_name

    def health_check(self) -> bool:
        """Verify AWS credentials/connection."""
        try:
            sts = self.session.client('sts')
            sts.get_caller_identity()
            return True
        except Exception:
            return False

    def get_lambda(self, function_name: str) -> 'LambdaFunction':
        return LambdaFunction(self.session, function_name)

    def get_s3_bucket(self, bucket_name: str) -> 'S3Bucket':
        return S3Bucket(self.session, bucket_name)


class LambdaFunction(CloudFunction):
    """AWS Lambda implementation."""

    def __init__(self, session, function_name: str):
        self.client = session.client('lambda')
        self.function_name = function_name

    def invoke(self, payload: Dict[str, Any]) -> Any:
        response = self.client.invoke(
            FunctionName=self.function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        return json.loads(response['Payload'].read().decode('utf-8'))

    def get_logs(self, limit: int = 10) -> List[str]:
        # Logs usually come from CloudWatch
        cw = boto3.client('logs')
        log_group_name = f"/aws/lambda/{self.function_name}"
        try:
            streams = cw.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=1
            )
            if not streams['logStreams']:
                return []
            
            stream_name = streams['logStreams'][0]['logStreamName']
            events = cw.get_log_events(
                logGroupName=log_group_name,
                logStreamName=stream_name,
                limit=limit
            )
            return [event['message'] for event in events['events']]
        except Exception:
            return []


class S3Bucket:
    """AWS S3 Bucket integration."""

    def __init__(self, session, bucket_name: str):
        self.s3 = session.resource('s3')
        self.bucket = self.s3.Bucket(bucket_name)

    def upload_file(self, local_path: str, key: str):
        self.bucket.upload_file(local_path, key)

    def download_file(self, key: str, local_path: str):
        self.bucket.download_file(key, local_path)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self.s3.Object(self.bucket.name, key).load()
            return True
        except ClientError:
            return False
