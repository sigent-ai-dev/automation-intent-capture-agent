aws_region    = "eu-west-1"
environment   = "dev"
project_name  = "intent-capture"
image_tag     = "latest"

# Cognito (already provisioned)
cognito_callback_urls = ["http://localhost:5174", "https://intent-capture-dev.example.com"]
cognito_logout_urls   = ["http://localhost:5174"]

# HTTP only for dev — no certificate needed
# For HTTPS, import a cert and set: certificate_arn = "arn:aws:acm:..."
certificate_arn = ""
