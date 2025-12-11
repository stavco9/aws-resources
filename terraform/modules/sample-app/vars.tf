variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "owner" {
  type = string
}

variable "app_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "instance_type" {
  type = string
}

variable "min_size" {
  type    = number
  default = 1
}

variable "max_size" {
  type    = number
  default = 3
}

variable "desired_capacity" {
  type    = number
  default = 2
}

variable "user_data_string" {
  type        = string
  default     = ""
  description = "User data string to be passed to the instance"
}

variable "volume_size_gb" {
  type    = number
  default = 30
}

variable "additional_iam_role_policies" {
  type    = map(string)
  default = {}
}

variable "app_backend_port" {
  type    = number
  default = 80
}

variable "app_backend_protocol" {
  type        = string
  default     = "HTTP"
  description = "The protocol to use for the backend"
}

variable "app_backend_health_check_path" {
  type        = string
  default     = "/"
  description = "The path to use for the backend health check"
}

variable "app_version" {
  type        = string
  description = "The version of the app"
}

variable "route53_zone_name" {
  type        = string
  description = "The name of the Route 53 zone to create the record in"
}

variable "route53_record_name" {
  type        = string
  description = "The name of the app to create the record in"
}

