output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "The ID of the VPC."
}

output "vpc_cidr" {
  value       = module.vpc.vpc_cidr_block
  description = "The CIDR block of the VPC."
}

output "private_subnet_ids" {
  value       = module.vpc.private_subnets
  description = "The IDs of the private subnets."
}

output "public_subnet_ids" {
  value       = module.vpc.public_subnets
  description = "The IDs of the public subnets."
}

output "subnet_azs" {
  value       = module.vpc.azs
  description = "The availability zones of the subnets."
}

output "vpc_endpoints" {
  value       = module.vpc_endpoints.endpoints
  description = "The endpoints of the VPC."
}