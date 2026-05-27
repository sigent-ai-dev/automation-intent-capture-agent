terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "intent-capture-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "intent-capture-tfstate-lock"
    encrypt        = true
  }
}
