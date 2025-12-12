# AWS Provider variables

variable "region" {
  type        = string
  description = "The region to deploy the VPC in."
  default     = "eu-central-1"
}

variable "profile" {
  type        = string
  description = "The profile to use for the AWS CLI."
  default     = "stav-devops"
}

# Project based variables

variable "project" {
  type        = string
  description = "The project name. Used for tagging and naming resources."
  default     = "365scores-devops"
}

variable "owner" {
  type        = string
  description = "The owner of the project. Used for tagging."
  default     = "stavco9@gmail.com"
}

variable "environment" {
  type        = string
  description = "The environment name. Used for tagging and naming resources."
  default     = "dev"
}

# VPC variables

variable "vpc_cidr" {
  type        = string
  description = "The CIDR block for the VPC"
  default     = "10.0.10.0/23"
}

variable "private_subnets" {
  type        = list(string)
  description = "The private subnets CIDR blocks for the VPC."
  default     = ["10.0.10.0/26", "10.0.10.64/26", "10.0.10.128/26"]
}

variable "public_subnets" {
  type        = list(string)
  description = "The public subnets CIDR blocks for the VPC."
  default     = ["10.0.11.0/26", "10.0.11.64/26", "10.0.11.128/26"]
}

variable "single_nat_gateway" {
  type        = bool
  description = "Whether to create a single NAT gateway for the VPC."
  default     = true
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Whether to enable NAT gateway for the VPC."
  default     = true
}

# VPC endpoints variables

variable "enable_s3_endpoint" {
  type        = bool
  description = "Whether to enable S3 endpoint for the VPC."
  default     = true
}