import boto3
import botocore
from typing import Optional


class StateBucket:
    def __init__(self, project: str, environment: str, owner: str, region: str, profile: Optional[str] = None):
        self.session = self.get_session(region, profile)
        self.region = self.get_session_region()
        self.account_id = self.get_session_account_id()

        self.tags = {
            "Project": project,
            "Environment": environment,
            "Owner": owner,
            "Region": region
        }

        print(f"Logged in to Account: {self.account_id} in Region: {self.region}")

    def convert_tags_to_tag_set(self) -> list[dict]:
        return [{'Key': key, 'Value': value} for key, value in self.tags.items()]

    def get_session(self, region: str, profile: Optional[str] = None) -> boto3.Session:
        try:
            return boto3.Session(region_name=region, profile_name=profile)
        except Exception as e:
            print(f"Error getting session: {e}")
            raise

    def get_session_account_id(self) -> str:
        account_id = self.session.client("sts").get_caller_identity()["Account"]
        
        if not account_id:
            raise RuntimeError("Account ID not found")

        return account_id

    def get_session_region(self) -> str:
        session_region = self.session.region_name

        if not session_region:
            raise RuntimeError("AWS region not found")

        return session_region


    def ensure_s3_bucket(self, bucket_name: str) -> None:
        """Create S3 bucket if missing. Enable versioning, encryption, and public access block.

        Idempotent: safe to call multiple times.
        """
        s3_client = self.session.client("s3", region_name=self.region)

        # Check existence
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            exists = True
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0))
            if error_code in (301, 404):
                exists = False
            else:
                # 403 can mean it exists but we have no access; re-raise to avoid accidental takeover
                raise

        if not exists:
            params = {"Bucket": bucket_name, "CreateBucketConfiguration": {"LocationConstraint": self.region}}
            s3_client.create_bucket(**params)

        # Block public access (account-level defaults don't always apply to new buckets)
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )

        # Default encryption: SSE-S3
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},
                        "BucketKeyEnabled": True,
                    }
                ]
            },
        )

        # Versioning for Terraform state
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"},
        )

        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={'TagSet': self.convert_tags_to_tag_set()}
        )

def main() -> None:
    owner = "stavco9@gmail.com"
    region = "eu-central-1"
    profile = "stav-devops"
    project = "365scores-devops"
    environment = "dev"
    state_bucket = StateBucket(project, environment, owner, region, profile)

    bucket_name = f"{state_bucket.account_id}-{state_bucket.region}-{project}-{environment}-terraform-state"

    state_bucket.ensure_s3_bucket(bucket_name)

    print(
        f"Ensured S3 bucket '{bucket_name}' in region '{state_bucket.region}'."
    )


if __name__ == "__main__":
    main()

