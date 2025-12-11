# AWS Resource Inventory Script

A Python script that discovers and exports detailed information about all AWS resources across multiple regions using AWS Resource Explorer and Cloud Control API.

## Overview

This script provides a comprehensive inventory of your AWS resources by:
1. **Discovering resources** using AWS Resource Explorer across specified regions
2. **Fetching detailed properties** for each resource using AWS Cloud Control API
3. **Exporting to CSV** with flexible grouping options (by region, by resource type, or both)

The CSV output includes all properties and details about each resource, such as:
- **EC2 Instances**: Instance type, AMI ID, VPC ID, Subnet ID, Security Groups, IAM Role, State, Launch Time, Tags, etc.
- **S3 Buckets**: Bucket name, Creation date, Versioning status, Encryption settings, Public access settings, Lifecycle rules, etc.
- **RDS Databases**: DB instance class, Engine version, Multi-AZ status, Storage type, Backup retention, Endpoint, etc.
- **DynamoDB Tables**: Table name, Billing mode (On-Demand/Provisioned), Read/Write capacity, Stream specification, Point-in-time recovery, etc.
- **SQS Queues**: Queue URL, Visibility timeout, Message retention, Dead letter queue configuration, etc.
- **Lambda Functions**: Runtime, Handler, Memory size, Timeout, Environment variables, VPC configuration, etc.
- **IAM Roles**: Trust policy, Permissions policies, Max session duration, etc.
- **VPCs**: CIDR blocks, DHCP options, DNS resolution, etc.
- And many more resource types with their complete properties

## Prerequisites

### 1. Enable AWS Resource Explorer

Before running the script, you must enable AWS Resource Explorer indexing:

1. Go to the [AWS Resource Explorer Console](https://resource-explorer.console.aws.amazon.com/resource-explorer/home)
2. Turn on resource indexing from one of your regions to all other regions you want to explore
3. Note the **aggregator region** (the region where the Resource Explorer index is aggregated) - you'll need this for the `--region` parameter

**Note**: Resource Explorer indexing may take some time to complete depending on the number of resources in your account.

### 2. Install Python Dependencies

```bash
pip install boto3
```

### 3. AWS Credentials

Ensure your AWS credentials are configured either via:
- AWS CLI profiles (`aws configure --profile <profile-name>`)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- IAM roles (if running on EC2)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install boto3
   ```
3. Configure your resource filters in `config.py` (optional, see Configuration section)

## Configuration

Edit `config.py` to customize resource filtering and mapping behavior:

### Whitelist Resource Types

Specify which resource types to include. Use `["*"]` to include all resource types:

```python
whitelist_resource_types = ["*"]  # Include all resource types

# Or specify specific types:
# whitelist_resource_types = [
#     'ec2:instance',
#     'rds:db',
#     'dynamodb:table',
#     's3:bucket',
#     'sqs:queue'
# ]
```

### Blacklist Resource Types

Specify resource types to exclude from the export:

```python
blacklist_resource_types = [
    'acm:certificate',
    'ec2:elastic-ip',
    'iam:policy',
    'ec2:network-interface',
    'ec2:security-group-rule'
]
```

**Note**: Blacklist takes precedence over whitelist. If a resource type is in both lists, it will be excluded.

### Resource Name Mappings

The script maps resource names from ARN format to Cloud Control API TypeName format. This mapping is essential because:
- Resource Explorer returns resources in ARN format (e.g., `ec2:instance`, `dynamodb:table`)
- Cloud Control API expects CloudFormation resource type format (e.g., `AWS::EC2::Instance`, `AWS::DynamoDB::Table`)

#### Adding New Mappings

If you encounter WARNING messages like:
```
Type AWS::<Service>::<Resource> not found for resource
```

This indicates that a resource type mapping is missing. To fix this:

1. **Identify the resource type** from the warning message and the ARN
2. **Check the Cloud Control API documentation** for the correct TypeName format: [Supported Resources](https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/supported-resources.html)
3. **Add the mapping** to `special_resource_group_name_mapping` in `config.py`:

```python
special_resource_group_name_mapping = {
    # Existing mappings...
    'your-resource-group-name': 'YourResourceGroupName',  # Add your mapping here
}
```

**Example**: If you see `Type AWS::EC2::ElasticIp not found`, you would add:
```python
special_resource_group_name_mapping = {
    # ... existing mappings
    'elastic-ip': 'EIP',  # Maps 'ec2:elastic-ip' to 'AWS::EC2::EIP'
}
```

The mapping converts the resource group name from the ARN (lowercase, hyphenated) to the Cloud Control API format (PascalCase).

#### Service-Specific Resource Group Mappings

Some services have special resource group name mappings that override the default camel case conversion:

```python
service_to_resource_group_name_mapping = {
    'S3': 'Bucket',      # Maps 's3:bucket' to 'AWS::S3::Bucket'
    'SQS': 'Queue'       # Maps 'sqs:queue' to 'AWS::SQS::Queue'
}
```

### Resource Identifier Configuration

The script extracts resource identifiers from ARNs differently based on service requirements:

#### Default Behavior
By default, the script extracts the resource ID from the ARN after the last slash (`/`):
- ARN: `arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0`
- Resource ID: `i-1234567890abcdef0`

#### Services Requiring Full ARN
Some services require the **full ARN** as the identifier. These are configured in `services_keep_service_arn`:

```python
services_keep_service_arn = [
    'ElasticLoadBalancingV2',  # ALB/NLB require full ARN
    'SecretsManager',           # Secrets require full ARN
    'AppRunner',                # App Runner services require full ARN
    'CE'                        # Cost Explorer resources require full ARN
]
```

#### Services with Different ARN Structure
Some services don't use the standard `arn:partition:service:region:account-id:resource-type/resource-id` format. Instead, they use:
- `arn:partition:service:region:account-id:resource-type:resource-id` (colon separator)
- `arn:partition:service:region:account-id:resource-id` (no resource type)

These are configured in `services_not_split_by_slash`:

```python
services_not_split_by_slash = [
    'RDS',          # Uses format: arn:aws:rds:region:account-id:db:db-instance-id
    'S3',           # Uses format: arn:aws:s3:::bucket-name
    'SQS',          # Uses format: arn:aws:sqs:region:account-id:queue-name
    'ElastiCache',  # Uses colon-separated format
    'Logs'          # CloudWatch Logs uses colon-separated format
]
```

For these services, the resource ID is extracted from the part after the last colon (`:`) instead of the last slash.

## Usage

### Basic Syntax

```bash
python list-resources.py --region <aggregator-region> [OPTIONS]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--region` | string | **Yes** | The AWS region where the Resource Explorer aggregator index exists. Find this in the [Resource Explorer Console](https://resource-explorer.console.aws.amazon.com/resource-explorer/home) |
| `--profile` | string | No | AWS profile name. If not specified, the default profile will be used |
| `--query-regions` | list | No | Space-separated list of AWS regions to query. For global services (IAM, Route53, etc.), specify `"global"`. Defaults to the `--region` value if not specified |
| `--log-level` | string | No | Log level: `INFO` (default), `DEBUG`, `WARNING`, or `ERROR` |
| `--output-by-region` | flag | No | Export one CSV file per region |
| `--output-by-resource-type` | flag | No | Export one CSV file per resource type |
| `--output-json` | flag | No | Export report in JSON format (in addition to CSV) |

### Output Options

The script supports flexible output grouping:

#### CSV Output Modes

- **No flags**: Single CSV file (`report.csv`) with all resources from all regions
- `--output-by-region`: One CSV file per region (e.g., `report_eu_central_1.csv`, `report_us_east_1.csv`)
  - When combined with `--output-by-resource-type`: One CSV file per region AND resource type (e.g., `report_ec2_instance_eu_central_1.csv`)
  - When used alone: One CSV file per region with all resource types combined
- `--output-by-resource-type`: One CSV file per resource type (e.g., `report_ec2_instance.csv`, `report_s3_bucket.csv`)
  - When used alone: One CSV file per resource type with all regions combined
  - When combined with `--output-by-region`: One CSV file per region AND resource type

#### JSON Output

- `--output-json`: Exports a single JSON file (`report.json`) containing all resources from all regions, regardless of other output options
  - This is in addition to CSV output (if any CSV flags are specified)
  - If no CSV flags are specified, only JSON will be exported

**Important Notes:**
- When `--output-by-region` is used, files are generated per region as resources are processed
- When `--output-by-region` is NOT used, all regions are combined into a single output
- JSON output always contains all resources from all regions in a single file

## Examples

### Example 1: Per-Region Report

Export resources grouped by region for multiple regions:

```bash
python list-resources.py \
    --profile stav-devops \
    --region eu-central-1 \
    --query-regions eu-central-1 us-east-1 global \
    --output-by-region
```

**Output**: 
- `report_eu_central_1.csv`
- `report_us_east_1.csv`
- `report_global.csv`

### Example 2: Per-Region-Per-Resource-Type Report

Export resources grouped by both region and resource type:

```bash
python list-resources.py \
    --profile stav-devops \
    --region eu-central-1 \
    --query-regions us-east-1 \
    --output-by-region \
    --output-by-resource-type
```

**Output**: 
- `report_ec2_instance_us_east_1.csv`
- `report_s3_bucket_us_east_1.csv`
- `report_rds_db_us_east_1.csv`
- ... (one file per resource type per region)

### Example 3: Debug Mode with Per-Region Report

Run with DEBUG log level to see detailed information:

```bash
python list-resources.py \
    --profile stav-devops \
    --region eu-central-1 \
    --query-regions us-east-1 \
    --output-by-region \
    --log-level DEBUG
```

### Example 4: Single Combined Report

Export all resources from multiple regions into a single CSV file:

```bash
python list-resources.py \
    --profile stav-devops \
    --region eu-central-1 \
    --query-regions us-east-1 us-east-2 global eu-central-1
```

**Output**: 
- `report.csv` (contains all resources from all specified regions)

### Example 5: Per-Resource-Type Report (All Regions Combined)

Export resources grouped by type across all regions:

```bash
python list-resources.py \
    --profile stav-devops \
    --region eu-central-1 \
    --query-regions us-east-1 us-east-2 eu-central-1 \
    --output-by-resource-type
```

**Output**: 
- `report_ec2_instance.csv` (all EC2 instances from all regions)
- `report_s3_bucket.csv` (all S3 buckets from all regions)
- `report_rds_db.csv` (all RDS databases from all regions)
- ... (one file per resource type)

### Example 6: Export with JSON Output

Export resources to both CSV (by region) and JSON:

```bash
python list-resources.py \
    --profile stav-devops \
    --region eu-central-1 \
    --query-regions us-east-1 us-east-2 \
    --output-by-region \
    --output-json
```

**Output**: 
- `report_us_east_1.csv` (CSV for us-east-1)
- `report_us_east_2.csv` (CSV for us-east-2)
- `report.json` (JSON with all resources from all regions)

## Output Format

### CSV Structure

Each CSV file contains:
- **Standard metadata columns** (present in all resources):
  - `Arn`: Full AWS Resource Name
  - `ResourceType`: Resource type (e.g., `ec2:instance`, `s3:bucket`)
  - `Region`: AWS region where the resource exists
  - `AccountId`: AWS account ID
  - `Service`: Service name (e.g., `EC2`, `S3`)
  - `ResourceGroup`: Resource group name (e.g., `Instance`, `Bucket`)
  - `Identifier`: Resource identifier used by Cloud Control API

- **Resource-specific properties**: All properties returned by Cloud Control API for that resource type

### Example Output Columns

#### EC2 Instance
```
Arn, ResourceType, Region, AccountId, Service, ResourceGroup, Identifier,
InstanceId, InstanceType, ImageId, VpcId, SubnetId, SecurityGroupIds,
IamInstanceProfile, State, LaunchTime, Tags, KeyName, ...
```

#### S3 Bucket
```
Arn, ResourceType, Region, AccountId, Service, ResourceGroup, Identifier,
BucketName, CreationDate, VersioningConfiguration, PublicAccessBlockConfiguration,
Encryption, LifecycleConfiguration, NotificationConfiguration, ...
```

#### RDS Database
```
Arn, ResourceType, Region, AccountId, Service, ResourceGroup, Identifier,
DBInstanceIdentifier, DBInstanceClass, Engine, EngineVersion, MultiAZ,
StorageType, AllocatedStorage, Endpoint, BackupRetentionPeriod, ...
```

#### DynamoDB Table
```
Arn, ResourceType, Region, AccountId, Service, ResourceGroup, Identifier,
TableName, BillingMode, AttributeDefinitions, KeySchema, ProvisionedThroughput,
StreamSpecification, PointInTimeRecoverySpecification, ...
```

## Troubleshooting

### Common Issues

1. **TypeNotFoundException**
   - Some resource types may not be supported by Cloud Control API, or a mapping may be missing
   - These resources will be skipped with a warning message: `Type AWS::<Service>::<Resource> not found for resource`
   - **Solution**: Add the missing mapping to `special_resource_group_name_mapping` in `config.py`
   - Check the [Cloud Control API Supported Resources](https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/supported-resources.html) documentation for the correct TypeName format
   - See the "Resource Name Mappings" section in Configuration for detailed instructions

2. **ThrottlingException**
   - AWS may throttle requests when processing many resources
   - The script will log errors for throttled resources
   - Consider running during off-peak hours or processing smaller batches

3. **Resource Explorer Not Indexed**
   - Ensure Resource Explorer is enabled and indexing is complete
   - Check the Resource Explorer console for indexing status
   - Wait for indexing to complete before running the script

4. **Incorrect Aggregator Region**
   - Verify the aggregator region in the Resource Explorer console
   - Use the correct region for the `--region` parameter

## Limitations

- **Cloud Control API Coverage**: Not all AWS resource types are supported by Cloud Control API. Unsupported types will be skipped with a warning. Check the [supported resources documentation](https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/supported-resources.html) for available types.
- **Rate Limits**: Cloud Control API has rate limits (~10 requests/second). Large inventories may take time to complete. The script will log throttling errors but does not automatically retry.
- **Global Services**: Global services (IAM, Route53, etc.) should be queried with `"global"` as the region in `--query-regions`.
- **Resource Name Mappings**: Some resource types may require manual mapping configuration in `config.py` if they're not already included. Watch for WARNING messages about TypeNotFound to identify missing mappings.

## Files

- `list-resources.py`: Main script
- `config.py`: Configuration file for whitelist/blacklist and resource type mappings
- `logger.py`: Logging configuration

## License

[Add your license information here]

## Contributing

[Add contribution guidelines if applicable]
