aws_region    = "eu-west-1"
environment   = "dev"
project_name  = "intent-capture"
image_tag     = "latest"

# Cognito (already provisioned)
cognito_callback_urls = ["http://localhost:5174", "https://intent-capture-dev.example.com"]
cognito_logout_urls   = ["http://localhost:5174"]

# Certificate ARN — import self-signed cert first (see environments/README.md)
# certificate_arn = "arn:aws:acm:eu-west-1:885659622434:certificate/REPLACE-AFTER-IMPORT"
