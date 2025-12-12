data "terraform_remote_state" "networking" {

  backend = "s3"
  config = {
    bucket  = var.remote_state_bucket
    key     = var.remote_state_networking_key
    profile = var.profile
    region  = var.remote_state_region
  }
}

module "sample_app" {
  source                        = "../../../../modules/sample-app"
  project                       = var.project
  environment                   = var.environment
  app_name                      = var.app_name
  vpc_id                        = data.terraform_remote_state.networking.outputs.vpc_id
  private_subnet_ids            = data.terraform_remote_state.networking.outputs.private_subnet_ids
  public_subnet_ids             = data.terraform_remote_state.networking.outputs.public_subnet_ids
  instance_type                 = var.instance_type
  min_size                      = var.min_size
  max_size                      = var.max_size
  desired_capacity              = var.desired_capacity
  owner                         = var.owner
  volume_size_gb                = var.volume_size_gb
  user_data_string              = file(var.user_data_path)
  app_backend_port              = var.app_backend_port
  app_backend_protocol          = var.app_backend_protocol
  app_backend_health_check_path = var.app_backend_health_check_path
  route53_zone_name             = var.route53_zone_name
  route53_record_name           = var.route53_record_name
  app_version                   = var.app_version
}