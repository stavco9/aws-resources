# Terraform Infrastructure as Code

This Terraform project provisions a production-ready AWS infrastructure setup with a sample application deployed behind an Application Load Balancer (ALB).

## Overview

This project sets up:

1. **Networking Infrastructure**:
   - VPC with public and private subnets across multiple Availability Zones
   - NAT Gateway(s) for private subnet internet access
   - Optional VPC endpoints (S3 Gateway endpoint)
   - Proper DNS configuration

2. **Sample Application Infrastructure**:
   - Application Load Balancer (ALB) in public subnets with HTTPS support
   - Auto Scaling Group (ASG) with EC2 instances in private subnets
   - ACM SSL/TLS certificate with automatic DNS validation
   - Route53 DNS records pointing to the ALB
   - Security groups with least-privilege access
   - ALB access logs to S3

## Architecture

```
Internet
   │
   ▼
Route53 DNS Record
   │
   ▼
Application Load Balancer (Public Subnets)
   │ (HTTPS/HTTP → HTTPS redirect)
   ▼
Target Group (Health Checks)
   │
   ▼
Auto Scaling Group (Private Subnets)
   │
   ▼
EC2 Instances (Sample App)
```

### Network Layout

```
VPC (10.0.0.0/16)
├── Public Subnets (Multi-AZ)
│   ├── ALB
│   └── NAT Gateway(s)
└── Private Subnets (Multi-AZ)
    └── EC2 Instances (ASG)
```

## Prerequisites

### 1. Terraform Installation

Install Terraform version 1.0 or later:

- **macOS**: `brew install terraform`
- **Linux**: Download from [terraform.io](https://www.terraform.io/downloads)
- **Windows**: Download from [terraform.io](https://www.terraform.io/downloads)

Verify installation:
```bash
terraform version
```

### 2. AWS Credentials Configuration

Configure AWS credentials using one of these methods:

- **AWS CLI Profile** (recommended):
  ```bash
  aws configure --profile <your-profile-name>
  ```

- **Environment Variables**:
  ```bash
  export AWS_ACCESS_KEY_ID="your-access-key"
  export AWS_SECRET_ACCESS_KEY="your-secret-key"
  export AWS_DEFAULT_REGION="eu-central-1"
  ```

- **IAM Role** (if running on EC2)

### 3. Create Remote State Bucket

Before running Terraform, you must create an S3 bucket for storing Terraform state:

```bash
cd terraform
python state_bucket.py
```

**Note**: Update the variables in `state_bucket.py` (project, environment, owner, region, profile) to match your setup.

The script will:
- Create an S3 bucket with versioning enabled
- Enable encryption (SSE-S3)
- Block public access
- Apply appropriate tags

**Bucket naming format**: `{account-id}-{region}-{project}-{environment}-terraform-state`

### 4. Route53 Hosted Zone

You must have a Route53 hosted zone in your AWS account for the domain where you want to deploy the application.

- The zone should be a **public hosted zone**
- Note the zone name (e.g., `example.com`)
- The script will create a subdomain record (e.g., `app.example.com`)

### 5. Apply Infrastructure in Order

The infrastructure must be applied in the correct order due to dependencies:

1. **First**: Apply the networking module
2. **Second**: Apply the sample-app module (depends on networking outputs)

## Quick Start

### Step 1: Configure Variables

Edit the variable files in `live/dev/eu-central-1/`:

**Networking variables** (`networking/vars.tf`):
- `vpc_cidr`: VPC CIDR block (e.g., `"10.0.0.0/16"`)
- `private_subnets`: List of private subnet CIDRs
- `public_subnets`: List of public subnet CIDRs
- `enable_nat_gateway`: Enable NAT Gateway (default: `true`)
- `single_nat_gateway`: Use single NAT Gateway for cost savings (default: `false`)

**Sample App variables** (`sample-app/vars.tf`):
- `route53_zone_name`: Your Route53 zone name (e.g., `"example.com"`)
- `route53_record_name`: Subdomain for the app (e.g., `"app"`)
- `instance_type`: EC2 instance type (e.g., `"t3.micro"`)
- `min_size`, `max_size`, `desired_capacity`: ASG scaling parameters
- `app_backend_port`: Application port (default: `8080`)
- `app_backend_health_check_path`: Health check path (e.g., `"/health"`)

### Step 2: Initialize Terraform

```bash
cd live/dev/eu-central-1/networking
terraform init
```

```bash
cd ../sample-app
terraform init
```

### Step 3: Apply Networking

```bash
cd live/dev/eu-central-1/networking
terraform plan
terraform apply
```

This creates:
- VPC with public and private subnets
- NAT Gateway(s)
- VPC endpoints (if enabled)
- Route tables and internet gateway

### Step 4: Apply Sample App

```bash
cd live/dev/eu-central-1/sample-app
terraform plan
terraform apply
```

This creates:
- Application Load Balancer
- Auto Scaling Group with EC2 instances
- ACM certificate and DNS validation
- Route53 DNS records
- Security groups
- ALB access logs bucket

## Security & Production-Ready Features

### High Availability & Resilience

1. **Multi-AZ Deployment**
   - ALB deployed across multiple Availability Zones
   - EC2 instances in private subnets across multiple AZs
   - Automatic failover if an AZ becomes unavailable

2. **Auto Scaling Group (ASG)**
   - Configurable min/max/desired capacity
   - Health checks based on ALB target group health
   - Automatic instance replacement for unhealthy instances

3. **Zero-Downtime Deployments**
   - **Instance Refresh with Rolling Strategy**: ASG supports rolling instance refresh
     - Checkpoints at 50%, 75%, and 100% completion
     - Minimum healthy percentage: 50% (ensures at least half instances remain healthy)
     - Maximum healthy percentage: 150% (allows temporary over-capacity during refresh)
     - Instance warmup: 120 seconds
     - Checkpoint delay: 180 seconds
   - New instances are launched and registered with the target group before old ones are terminated
   - ALB health checks ensure traffic only routes to healthy instances

4. **Application Load Balancer Features**
   - **Health Checks**: Configurable health check path, protocol, and status codes (200-302)
   - **Target Health Evaluation**: Route53 records evaluate target health
   - **Access Logs**: All ALB requests logged to S3 for monitoring and debugging
   - **HTTP to HTTPS Redirect**: Automatic redirect from port 80 to 443

### Security Features

1. **Network Security**
   - EC2 instances in **private subnets** (no direct internet access)
   - ALB in **public subnets** (only entry point from internet)
   - Security groups with least-privilege rules:
     - ALB: Allows HTTP (80) and HTTPS (443) from internet
     - EC2: Allows traffic only from ALB security group on application port
   - VPC endpoints for S3 (optional) to avoid internet traffic for S3 access

2. **Encryption**
   - **EBS Volumes**: Encrypted at rest (default encryption enabled)
   - **In-Transit**: HTTPS/TLS encryption via ACM certificate
   - **S3 Buckets**: Server-side encryption enabled (SSE-S3)

3. **SSL/TLS Certificate Management**
   - ACM certificate automatically created and validated via DNS
   - Automatic DNS validation records created in Route53
   - Certificate lifecycle management (create before destroy)

4. **IAM Security**
   - EC2 instances have IAM instance profiles with minimal permissions:
     - `AmazonSSMManagedInstanceCore`: For Systems Manager Session Manager access
     - `AmazonEC2ContainerRegistryReadOnly`: For ECR access (if using containers)
   - Additional IAM policies can be added via variables

5. **Monitoring & Logging**
   - **CloudWatch Monitoring**: Enhanced monitoring enabled for EC2 instances
   - **ALB Access Logs**: Comprehensive request logging to S3
   - **Health Checks**: ALB and ASG health checks for automatic recovery

### Operational Excellence

1. **Infrastructure as Code**
   - All infrastructure defined in Terraform
   - Version controlled and repeatable
   - Remote state stored in S3 with versioning

2. **Tagging Strategy**
   - Consistent tagging across all resources:
     - `Environment`: Environment name (dev, staging, prod)
     - `Project`: Project identifier
     - `Owner`: Resource owner
     - `Region`: AWS region
     - `ManagedBy`: "terraform"
   - Enables cost tracking and resource management

3. **Cost Optimization**
   - Option for single NAT Gateway (cost savings in non-production)
   - Configurable instance types and ASG sizing
   - EBS-optimized instances for better performance/cost ratio
   - GP3 volumes (latest generation, cost-effective)

4. **Disaster Recovery**
   - S3 bucket versioning for Terraform state
   - State file backups enable infrastructure recreation
   - Multi-AZ deployment provides AZ-level redundancy

## Module Structure

```
terraform/
├── modules/
│   ├── networking/          # VPC, subnets, NAT Gateway, VPC endpoints
│   └── sample-app/          # ALB, ASG, ACM, Route53, Security Groups
├── live/
│   └── dev/
│       └── eu-central-1/
│           ├── networking/  # Networking module instantiation
│           └── sample-app/  # Sample app module instantiation
└── state_bucket.py          # Script to create remote state bucket
```

## Outputs

### Networking Module Outputs

- `vpc_id`: VPC ID
- `vpc_cidr`: VPC CIDR block
- `private_subnet_ids`: List of private subnet IDs
- `public_subnet_ids`: List of public subnet IDs
- `subnet_azs`: Availability zones used
- `vpc_endpoints`: VPC endpoint information

### Sample App Module Outputs

- `asg_name`: Auto Scaling Group name
- `asg_id`: Auto Scaling Group ID
- `sample_app_alb_dns_name`: ALB DNS name
- `sample_app_alb_id`: ALB ID
- `sample_app_route53_records`: Route53 record information
- `sample_app_sg_id`: Security group ID
- `sample_app_iam_role_arn`: IAM role ARN

## Customization

### Adding Additional IAM Policies

Edit `sample-app/vars.tf` and add policies to `additional_iam_role_policies`:

```hcl
variable "additional_iam_role_policies" {
  type = map(string)
  default = {
    MyCustomPolicy = "arn:aws:iam::aws:policy/MyCustomPolicy"
  }
}
```

### Modifying User Data

Edit the user data script at `live/dev/eu-central-1/sample-app/user-data.sh` or update the `user_data_path` variable to point to your custom script.

### Changing Instance Refresh Settings

Modify the `instance_refresh` block in `modules/sample-app/asg.tf`:

```hcl
instance_refresh = {
  strategy = "Rolling"
  preferences = {
    checkpoint_percentages = [25, 50, 75, 100]  # Custom checkpoints
    checkpoint_delay       = 300                 # 5 minutes
    instance_warmup        = 180                 # 3 minutes
    min_healthy_percentage = 50
    max_healthy_percentage = 150
  }
  triggers = ["tag"]
}
```

## Troubleshooting

### State Lock Issues

If Terraform state is locked:
```bash
# Check for locks in S3
aws s3api head-object --bucket <state-bucket> --key <state-key>

# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

### Instance Refresh Not Triggering

Instance refresh is triggered by tag changes. To manually trigger:
```bash
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name <asg-name> \
  --preferences MinHealthyPercentage=50,InstanceWarmup=120
```

### Health Check Failures

- Verify application is listening on the configured port
- Check security group rules allow ALB → EC2 traffic
- Ensure health check path returns 200-302 status codes
- Review CloudWatch logs and ALB access logs

## Cost Estimation

Approximate monthly costs (varies by region and usage):

- **NAT Gateway**: ~$32/month per gateway (data transfer additional)
- **ALB**: ~$16/month + $0.008 per LCU-hour
- **EC2 Instances**: Varies by instance type and usage
- **EBS Volumes**: ~$0.10/GB/month for GP3
- **Route53**: $0.50/month per hosted zone + $0.40 per million queries

**Cost Optimization Tips**:
- Use `single_nat_gateway = true` for non-production environments
- Use smaller instance types for development
- Consider Reserved Instances for production workloads

## Best Practices

1. **State Management**: Never commit `.tfstate` files to version control
2. **Secrets**: Use AWS Secrets Manager or Parameter Store for sensitive data
3. **Backup**: Enable S3 versioning for state bucket
4. **Testing**: Test changes in dev environment before production
5. **Documentation**: Update this README when making significant changes
6. **Tagging**: Maintain consistent tagging strategy
7. **Monitoring**: Set up CloudWatch alarms for critical metrics

## Support

For issues or questions:
1. Check Terraform plan output for errors
2. Review AWS CloudWatch logs
3. Verify IAM permissions
4. Check security group rules
5. Review ALB access logs in S3
