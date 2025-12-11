output "asg_name" {
  value = module.asg.autoscaling_group_name
}

output "asg_id" {
  value = module.asg.autoscaling_group_id
}

output "asg_arn" {
  value = module.asg.autoscaling_group_arn
}

output "sample_app_sg_id" {
  value = aws_security_group.sample_app_sg.id
}

output "sample_app_iam_role_arn" {
  value = module.asg.iam_role_arn
}