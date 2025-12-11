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

Edit `config.py` to customize which resources are included in the export:

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

### Output Options

The script supports flexible output grouping:

- **No flags**: Single CSV file with all resources from all regions
- `--output-by-region`: One CSV file per region (e.g., `report_eu_central_1.csv`, `report_us_east_1.csv`)
- `--output-by-resource-type`: One CSV file per resource type (e.g., `report_ec2_instance.csv`, `report_s3_bucket.csv`)
- **Both flags**: One CSV file per region AND resource type combination (e.g., `report_ec2_instance_eu_central_1.csv`)

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
   - Some resource types may not be supported by Cloud Control API
   - These resources will be skipped with a warning message
   - Check the logs for details

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

- **Cloud Control API Coverage**: Not all AWS resource types are supported by Cloud Control API. Unsupported types will be skipped.
- **Rate Limits**: Cloud Control API has rate limits (~10 requests/second). Large inventories may take time to complete.
- **Global Services**: Global services (IAM, Route53, etc.) should be queried with `"global"` as the region in `--query-regions`.

## Files

- `list-resources.py`: Main script
- `config.py`: Configuration file for whitelist/blacklist and resource type mappings
- `logger.py`: Logging configuration

## License

[Add your license information here]

## Contributing

[Add contribution guidelines if applicable]
