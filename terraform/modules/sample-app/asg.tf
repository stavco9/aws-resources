
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"] # Amazon's official AMI owner ID

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

resource "aws_security_group" "sample_app_sg" {
  name        = format("%s-%s-%s-sg", var.project, var.environment, var.app_name)
  description = "Allow inbound traffic from the load balancer and all outbound traffic to the internet"
  vpc_id      = var.vpc_id

  tags = local.tags
}

resource "aws_security_group_rule" "outbound_traffic" {
  security_group_id = aws_security_group.sample_app_sg.id
  type              = "egress"
  protocol          = "-1"
  from_port         = 0
  to_port           = 0
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "ingress_traffic" {
  security_group_id        = aws_security_group.sample_app_sg.id
  type                     = "ingress"
  protocol                 = "tcp"
  from_port                = var.app_backend_port
  to_port                  = var.app_backend_port
  source_security_group_id = module.alb.security_group_id
}

module "asg" {
  source = "terraform-aws-modules/autoscaling/aws"

  # Autoscaling group
  name = format("%s-%s-%s-asg", var.project, var.environment, var.app_name)

  min_size            = var.min_size
  max_size            = var.max_size
  desired_capacity    = var.desired_capacity
  health_check_type   = "ELB"
  vpc_zone_identifier = var.private_subnet_ids

  # Launch template
  launch_template_name   = format("%s-%s-%s-lt", var.project, var.environment, var.app_name)
  update_default_version = true

  image_id          = data.aws_ami.amazon_linux.id
  instance_type     = var.instance_type
  ebs_optimized     = true
  enable_monitoring = true

  # IAM role & instance profile
  create_iam_instance_profile = true
  iam_role_name               = substr(format("%s-%s-%s-%s-asg", var.project, var.environment, data.aws_region.current.name, var.app_name), 0, 31)
  iam_role_path               = "/ec2/"
  iam_role_description        = "IAM role example"
  iam_role_tags               = local.tags
  iam_role_policies = merge({
    AmazonSSMManagedInstanceCore       = local.ssm_policy
    AmazonEC2ContainerRegistryReadOnly = local.ecr_read_only_policy
  }, var.additional_iam_role_policies)

  security_groups = [aws_security_group.sample_app_sg.id]

  user_data = base64encode(var.user_data_string)

  instance_refresh = {
    strategy = "Rolling"
    preferences = {
      checkpoint_percentages = [50, 75, 100]
      checkpoint_delay       = 180
      instance_warmup        = 120
      min_healthy_percentage = 50
      max_healthy_percentage = 150
    }
    triggers = ["tag"]
  }

  block_device_mappings = [
    {
      # Root volume
      device_name = "/dev/xvda"
      no_device   = 0
      ebs = {
        delete_on_termination = true
        encrypted             = true
        volume_size           = var.volume_size_gb
        volume_type           = "gp3"
      }
    }
  ]

  tag_specifications = [
    {
      resource_type = "instance"
      tags          = local.tags
    },
    {
      resource_type = "volume"
      tags          = local.tags
    }
  ]

  traffic_source_attachments = {
    app_backend = {
      traffic_source_identifier = aws_lb_target_group.app_backend_target_group.arn
      traffic_source_type       = "elbv2"
    }
  }

  tags = merge(local.tags, {
    version = var.app_version
  })
}