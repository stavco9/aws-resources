module "alb-access-log-bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 5.0"

  bucket = substr(format("%s-%s-%s-%s-%s-alb-access-log",
    data.aws_caller_identity.current.account_id,
    data.aws_region.current.name,
    var.project,
    var.environment,
  var.app_name), 0, 63)

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  attach_elb_log_delivery_policy = true # Required for ALB logs
  attach_lb_log_delivery_policy  = true # Required for ALB/NLB logs

  tags = local.tags
}

resource "aws_lb_target_group" "app_backend_target_group" {
  name     = substr(format("%s-%s-%s-tg", var.project, var.environment, var.app_name), 0, 31)
  port     = var.app_backend_port
  protocol = var.app_backend_protocol
  vpc_id   = var.vpc_id

  health_check {
    path     = var.app_backend_health_check_path
    protocol = var.app_backend_protocol
    matcher  = "200-302"
  }

  tags = local.tags
}

module "alb" {
  source = "terraform-aws-modules/alb/aws"

  name    = substr(format("%s-%s-%s-alb", var.project, var.environment, var.app_name), 0, 31)
  vpc_id  = var.vpc_id
  subnets = var.public_subnet_ids

  # Security Group
  security_group_ingress_rules = {
    all_http = {
      from_port   = 80
      to_port     = 80
      ip_protocol = "tcp"
      description = "HTTP web traffic"
      cidr_ipv4   = "0.0.0.0/0"
    }
    all_https = {
      from_port   = 443
      to_port     = 443
      ip_protocol = "tcp"
      description = "HTTPS web traffic"
      cidr_ipv4   = "0.0.0.0/0"
    }
  }
  security_group_egress_rules = {
    all = {
      from_port                    = var.app_backend_port
      to_port                      = var.app_backend_port
      ip_protocol                  = "tcp"
      referenced_security_group_id = aws_security_group.sample_app_sg.id
    }
  }

  access_logs = {
    bucket = module.alb-access-log-bucket.s3_bucket_id
  }

  listeners = {
    ex-http-https-redirect = {
      port     = 80
      protocol = "HTTP"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
    ex-https = {
      port            = 443
      protocol        = "HTTPS"
      certificate_arn = aws_acm_certificate.master_cert.arn

      forward = {
        target_group_arn = aws_lb_target_group.app_backend_target_group.arn
      }
    }
  }

  route53_records = {
    main = {
      zone_id                = data.aws_route53_zone.dns_zone.zone_id
      name                   = var.route53_record_name
      type                   = "A"
      evaluate_target_health = true
    }
  }

  tags = local.tags
}