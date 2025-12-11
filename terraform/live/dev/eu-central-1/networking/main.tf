module "networking" {
  source = "../../../../modules/networking"

  vpc_cidr = "10.0.10.0/23"

  project         = "365scores-devops"
  owner           = "stavco9@gmail.com"
  environment     = "dev"
  private_subnets = ["10.0.10.0/26", "10.0.10.64/26", "10.0.10.128/26"]
  public_subnets  = ["10.0.11.0/26", "10.0.11.64/26", "10.0.11.128/26"]

  single_nat_gateway = true
  enable_nat_gateway = true
  enable_s3_endpoint = true
}