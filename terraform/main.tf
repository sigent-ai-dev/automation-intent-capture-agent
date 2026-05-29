module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  environment  = var.environment
}

module "voice_service" {
  source = "./modules/voice-service"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  image_tag            = var.image_tag
  certificate_arn      = var.certificate_arn
  vpc_id               = module.networking.vpc_id
  public_subnet_ids    = module.networking.public_subnet_ids
  private_subnet_ids   = module.networking.private_subnet_ids
  cognito_user_pool_id = module.cognito.user_pool_id
}

module "cognito" {
  source = "./modules/cognito"

  project_name      = var.project_name
  environment       = var.environment
  callback_urls     = var.cognito_callback_urls
  logout_urls       = var.cognito_logout_urls
  enable_federation = var.cognito_enable_federation
}

module "cicd" {
  source = "./modules/cicd"

  project_name = var.project_name
  environment  = var.environment
  github_org   = "sigent-ai-dev"
  github_repo  = "automation-intent-capture-agent"
}
