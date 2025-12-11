data "terraform_remote_state" "networking" {

  backend = "s3"
  config = {
    bucket  = "882709358319-eu-central-1-365scores-devops-dev-terraform-state"
    key     = "dev/eu-central-1/networking/terraform.tfstate"
    profile = "stav-devops"
    region  = "eu-central-1"
  }
}

module "sample_app" {
  source                        = "../../../../modules/sample-app"
  project                       = "365scores"
  environment                   = "dev"
  app_name                      = "sample-app"
  vpc_id                        = data.terraform_remote_state.networking.outputs.vpc_id
  private_subnet_ids            = data.terraform_remote_state.networking.outputs.private_subnet_ids
  public_subnet_ids             = data.terraform_remote_state.networking.outputs.public_subnet_ids
  instance_type                 = "t3.small"
  min_size                      = 1
  max_size                      = 3
  desired_capacity              = 2
  owner                         = "stavco9@gmail.com"
  volume_size_gb                = 30
  user_data_string              = file("user-data.sh")
  app_backend_port              = 8080
  app_backend_protocol          = "HTTP"
  app_backend_health_check_path = "/"
  route53_zone_name             = "stavco9.com"
  route53_record_name           = "sample-app.dev.365scores"
  app_version                   = "1.0.1"
}