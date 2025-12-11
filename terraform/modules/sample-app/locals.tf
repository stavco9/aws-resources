locals {
  tags = {
    Environment = var.environment
    Region      = data.aws_region.current.name
    Project     = var.project
    Owner       = var.owner
    AppName     = var.app_name
    ManagedBy   = "terraform"
  }

  ssm_policy           = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  ecr_read_only_policy = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_route53_zone" "dns_zone" {
  name         = var.route53_zone_name
  private_zone = false
}