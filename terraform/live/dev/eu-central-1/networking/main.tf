module "networking" {
  source = "../../../../modules/networking"

  vpc_cidr = var.vpc_cidr

  project         = var.project
  owner           = var.owner
  environment     = var.environment
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  single_nat_gateway = var.single_nat_gateway
  enable_nat_gateway = var.enable_nat_gateway
  enable_s3_endpoint = var.enable_s3_endpoint
}