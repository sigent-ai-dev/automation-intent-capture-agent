variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "callback_urls" {
  description = "Allowed callback URLs for the SPA client (app URL + localhost for dev)"
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "logout_urls" {
  description = "Allowed logout URLs for the SPA client"
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "enable_federation" {
  description = "Whether to enable federated identity providers"
  type        = bool
  default     = false
}
