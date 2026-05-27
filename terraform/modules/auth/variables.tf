variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "alb_arn" {
  type        = string
  description = "ARN of the ALB to associate WAF with"
}

variable "callback_urls" {
  type        = list(string)
  default     = ["http://localhost:5173"]
  description = "Allowed callback URLs for Cognito app client"
}

variable "logout_urls" {
  type        = list(string)
  default     = ["http://localhost:5173"]
  description = "Allowed logout URLs for Cognito app client"
}

variable "waf_rate_limit" {
  type    = number
  default = 100
}

variable "waf_body_size_limit" {
  type    = number
  default = 8192
}
