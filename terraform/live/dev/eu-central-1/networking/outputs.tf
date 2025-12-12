output "vpc_id" {
  value       = module.networking.vpc_id
  description = "The ID of the VPC."
}

output "private_subnet_ids" {
  value       = module.networking.private_subnet_ids
  description = "The IDs of the private subnets."
}

output "public_subnet_ids" {
  value       = module.networking.public_subnet_ids
  description = "The IDs of the public subnets."
}

output "vpc_cidr" {
  value       = module.networking.vpc_cidr
  description = "The CIDR block of the VPC."
}

output "subnet_azs" {
  value       = module.networking.subnet_azs
  description = "The availability zones of the subnets."
}

output "vpc_endpoints" {
  value       = module.networking.vpc_endpoints
  description = "The endpoints of the VPC."
}