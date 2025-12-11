terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "882709358319-eu-central-1-365scores-devops-dev-terraform-state"
    key          = "dev/eu-central-1/sample-app/terraform.tfstate"
    use_lockfile = true
    profile      = "stav-devops"
    region       = "eu-central-1"
  }
}

# Configure the AWS Provider
provider "aws" {
  profile = "stav-devops"
  region  = "eu-central-1"
}