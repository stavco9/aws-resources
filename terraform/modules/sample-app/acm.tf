resource "aws_acm_certificate" "master_cert" {
  domain_name       = "${var.route53_record_name}.${var.route53_zone_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.tags, {
    Name = "${var.route53_record_name}.${var.route53_zone_name}"
  })
}

resource "aws_route53_record" "master_cert_validate" {
  for_each = {
    for dvo in aws_acm_certificate.master_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.dns_zone.zone_id
}

resource "aws_acm_certificate_validation" "master_cert_validate" {
  certificate_arn         = aws_acm_certificate.master_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.master_cert_validate : record.fqdn]
}
