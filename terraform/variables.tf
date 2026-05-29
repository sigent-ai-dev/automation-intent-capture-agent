variable "aws_region" {
  type        = string
  description = "AWS region for all resources"
  default     = "eu-west-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  default     = "dev"
}

variable "project_name" {
  type        = string
  description = "Project name used for resource naming"
  default     = "intent-capture"
}

variable "image_tag" {
  type        = string
  description = "Container image tag to deploy"
  default     = "latest"
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS on the ALB (empty = HTTP only for dev)"
  default     = ""
}

variable "cognito_callback_urls" {
  type        = list(string)
  description = "Allowed callback URLs for Cognito SPA client"
  default     = ["http://localhost:5173"]
}

variable "cognito_logout_urls" {
  type        = list(string)
  description = "Allowed logout URLs for Cognito SPA client"
  default     = ["http://localhost:5173"]
}

variable "cognito_enable_federation" {
  type        = bool
  description = "Enable federated identity providers in Cognito"
  default     = false
}
