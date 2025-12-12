output "asg_name" {
  value       = module.sample_app.asg_name
  description = "The name of the autoscaling group."
}

output "asg_id" {
  value       = module.sample_app.asg_id
  description = "The ID of the autoscaling group."
}

output "asg_arn" {
  value       = module.sample_app.asg_arn
  description = "The ARN of the autoscaling group."
}

output "sample_app_sg_id" {
  value       = module.sample_app.sample_app_sg_id
  description = "The ID of the security group."
}

output "sample_app_iam_role_arn" {
  value       = module.sample_app.sample_app_iam_role_arn
  description = "The ARN of the IAM role attached to the autoscaling group."
}

output "sample_app_alb_arn" {
  value       = module.sample_app.sample_app_alb_arn
  description = "The ARN of the application load balancer."
}

output "sample_app_alb_id" {
  value       = module.sample_app.sample_app_alb_id
  description = "The ID of the application load balancer."
}

output "sample_app_alb_dns_name" {
  value       = module.sample_app.sample_app_alb_dns_name
  description = "The DNS name of the application load balancer."
}

output "sample_app_route53_records" {
  value       = module.sample_app.sample_app_route53_records
  description = "The Route 53 records attached to the application load balancer."
}