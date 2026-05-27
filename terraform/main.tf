module "voice_service" {
  source = "./modules/voice-service"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  image_tag          = var.image_tag
  certificate_arn    = var.certificate_arn
  vpc_id             = var.vpc_id
  public_subnet_ids  = var.public_subnet_ids
  private_subnet_ids = var.private_subnet_ids
}
