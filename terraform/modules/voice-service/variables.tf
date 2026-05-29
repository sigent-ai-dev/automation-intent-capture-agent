variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS listener (empty string = HTTP only)"
  default     = ""
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "task_cpu" {
  type    = number
  default = 512
}

variable "task_memory" {
  type    = number
  default = 1024
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "max_count" {
  type    = number
  default = 10
}

variable "min_count" {
  type    = number
  default = 1
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "health_check_path" {
  type    = string
  default = "/health/live"
}

variable "cognito_user_pool_id" {
  type        = string
  description = "Cognito user pool ID for JWT validation"
  default     = ""
}

variable "websocket_idle_timeout" {
  type        = number
  default     = 1800
  description = "ALB idle timeout in seconds (30min for WebSocket)"
}

variable "log_retention_days" {
  type    = number
  default = 30
}
