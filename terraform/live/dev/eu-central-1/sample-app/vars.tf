

# AWS Provider variables

variable "region" {
  type        = string
  description = "The region to deploy the sample app in."
  default     = "eu-central-1"
}

variable "profile" {
  type        = string
  description = "The profile to use for the AWS CLI."
  default     = "stav-devops"
}

# Remote state variables

variable "remote_state_bucket" {
  type        = string
  description = "The name of the remote state bucket."
  default     = "882709358319-eu-central-1-365scores-devops-dev-terraform-state"
}

variable "remote_state_networking_key" {
  type        = string
  description = "The key of the remote state file for the networking module."
  default     = "dev/eu-central-1/networking/terraform.tfstate"
}

variable "remote_state_region" {
  type        = string
  description = "The region of the remote state bucket."
  default     = "eu-central-1"
}

# Project based variables

variable "project" {
  type        = string
  description = "The project name. Used for tagging and naming resources."
  default     = "365scores"
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

# Sample app variables

variable "app_name" {
  type        = string
  description = "The name of the sample app. Used for tagging and naming resources."
  default     = "sample-app"
}

variable "app_version" {
  type        = string
  description = "The version of the app. Please note that modifying this value triggers the instance refresh of the autoscaling group."
  default     = "1.0.1"
}

# Autoscaling group variables

variable "instance_type" {
  type        = string
  description = "The instance type to use for the sample app."
  default     = "t3.small"
}

variable "min_size" {
  type        = number
  description = "The minimum number of instances to run in the sample app."
  default     = 1
}

variable "max_size" {
  type        = number
  description = "The maximum number of instances to run in the sample app."
  default     = 3
}

variable "desired_capacity" {
  type        = number
  description = "The desired number of instances to run in the sample app."
  default     = 2
}

variable "volume_size_gb" {
  type        = number
  description = "The size of the volume in GB to use for the sample app."
  default     = 30
}

variable "user_data_path" {
  type        = string
  description = "The path to the user data file to use for the sample app."
  default     = "user-data.sh"
}

# App Load Balancer variables

variable "app_backend_port" {
  type        = number
  description = "The port to use for the backend of the sample app."
  default     = 8080
}

variable "app_backend_protocol" {
  type        = string
  description = "The protocol to use for the backend of the sample app."
  default     = "HTTP"
}

variable "app_backend_health_check_path" {
  type        = string
  description = "The path to use for the backend health check of the sample app."
  default     = "/"
}

# Route 53 variables

variable "route53_zone_name" {
  type        = string
  description = "The name of the Route 53 zone to create the record in."
  default     = "stavco9.com"
}

variable "route53_record_name" {
  type        = string
  description = "The name of the app to create the record in."
  default     = "sample-app.dev.365scores"
}