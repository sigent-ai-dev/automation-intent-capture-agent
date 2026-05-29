output "deploy_role_arn" {
  description = "IAM role ARN for GitHub Actions deployment"
  value       = aws_iam_role.deploy.arn
}
