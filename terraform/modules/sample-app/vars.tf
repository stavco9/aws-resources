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

# App variables

variable "app_name" {
  type        = string
  description = "The name of the app. Used for tagging and naming resources."
}

variable "app_version" {
  type        = string
  description = "The version of the app. Please note that modifying this value triggers the instance refresh of the autoscaling group."
}

# VPC variables

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC to deploy the app in."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "The IDs of the private subnets to deploy the app instances in."
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "The IDs of the public subnets to deploy the app load balancer in."
}

# Autoscaling group variables

variable "instance_type" {
  type        = string
  description = "The instance type to use for the app."
}

variable "min_size" {
  type        = number
  description = "The minimum number of instances to run in the app."
  default     = 1
}

variable "max_size" {
  type        = number
  description = "The maximum number of instances to run in the app."
  default     = 3
}

variable "desired_capacity" {
  type        = number
  description = "The desired number of instances to run in the app."
  default     = 2
}

variable "user_data_string" {
  type        = string
  default     = ""
  description = "The user data string to be passed to the instance"
}

variable "volume_size_gb" {
  type        = number
  description = "The size of the volume in GB to use for the app."
  default     = 30
}

variable "additional_iam_role_policies" {
  type        = map(string)
  description = "The additional IAM role policies to add to the app."
  default     = {}
}

# App Load Balancer variables

variable "app_backend_port" {
  type        = number
  description = "The port to use for the backend of the app (The internal port of the app)."
  default     = 80
}

variable "app_backend_protocol" {
  type        = string
  description = "The protocol to use for the backend (The protocol of the app)."
  default     = "HTTP"
}

variable "app_backend_health_check_path" {
  type        = string
  description = "The path to use for the backend health check (The path to check if the app is healthy)."
  default     = "/"
}

# Route 53 variables

variable "route53_zone_name" {
  type        = string
  description = "The name of the Route 53 zone to create the record in."
}

variable "route53_record_name" {
  type        = string
  description = "The name of the app to create the record in."
}

