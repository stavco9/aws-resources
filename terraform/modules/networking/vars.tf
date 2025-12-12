# Project based variables

variable "project" {
  type        = string
  description = "The project name. Used for tagging and naming resources."
}

variable "environment" {
  type        = string
  description = "The environment name. Used for tagging and naming resources."
}

variable "owner" {
  type        = string
  description = "The owner of the project. Used for tagging."
}

# VPC variables

variable "vpc_cidr" {
  type        = string
  description = "The CIDR block for the VPC"
}

variable "private_subnets" {
  type        = list(string)
  description = "The private subnets CIDR blocks for the VPC."
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Whether to enable NAT gateway for the VPC."
  default     = true
}

variable "single_nat_gateway" {
  type        = bool
  description = "Whether to create a single NAT gateway for the VPC."
  default     = true
}

variable "public_subnets" {
  description = "The public subnets CIDR blocks for the VPC."
  type        = list(string)
}

# VPC endpoints variables

variable "enable_s3_endpoint" {
  type        = bool
  description = "Whether to enable S3 endpoint for the VPC."
  default     = false
}