output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.voice_service.alb_dns_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing container images"
  value       = module.voice_service.ecr_repository_url
}

output "service_url" {
  description = "HTTPS URL for the voice service"
  value       = module.voice_service.service_url
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = module.voice_service.cluster_name
}
