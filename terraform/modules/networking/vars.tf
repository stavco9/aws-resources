variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "owner" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "private_subnets" {
  type = list(string)
}

variable "enable_nat_gateway" {
  type = bool

  default = true
}

variable "single_nat_gateway" {
  type = bool

  default = true
}

variable "public_subnets" {
  type = list(string)
}

variable "enable_s3_endpoint" {
  type = bool

  default = false
}