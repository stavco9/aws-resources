data "aws_availability_zones" "all_az" {
  state = "available"
}

locals {
  tags = {
    Environment = var.environment
    Region      = data.aws_region.current.name
    Project     = var.project
    Owner       = var.owner
    ManagedBy   = "terraform"
  }

  vpc_name = format("%s-%s", var.project, var.environment)

  create_endpoints = anytrue([var.enable_s3_endpoint])
}

data "aws_region" "current" {}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = local.vpc_name
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.all_az.names, 0, length(var.private_subnets))
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway   = var.enable_nat_gateway
  single_nat_gateway   = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, {
    Name = local.vpc_name
  })

  private_subnet_tags = {
    Name   = format("%s-private", local.vpc_name)
    Access = "private"
  }

  public_subnet_tags = {
    Name   = format("%s-public", local.vpc_name)
    Access = "public"
  }
}

module "vpc_endpoints" {
  source = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"

  create = local.create_endpoints

  vpc_id = module.vpc.vpc_id

  endpoints = {
    s3 = var.enable_s3_endpoint ? {
      service         = "s3"
      service_type    = "Gateway"
      route_table_ids = module.vpc.private_route_table_ids
      tags = {
        Name        = format("%s-s3-endpoint", local.vpc_name),
        ServiceType = "Gateway"
      }
    } : null
  }

  tags = local.tags
}