# Environment Configuration

## Self-Signed Certificate (Dev Only)

Generate and import a self-signed certificate for the dev ALB HTTPS listener:

```bash
# Generate certificate (valid 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/intent-capture-dev-key.pem \
  -out /tmp/intent-capture-dev-cert.pem \
  -subj "/CN=intent-capture-dev"

# Import to ACM
CERT_ARN=$(aws acm import-certificate \
  --certificate fileb:///tmp/intent-capture-dev-cert.pem \
  --private-key fileb:///tmp/intent-capture-dev-key.pem \
  --region eu-west-1 \
  --profile sigent+builder-Admin \
  --query 'CertificateArn' --output text)

echo "Add to dev.tfvars: certificate_arn = \"$CERT_ARN\""
```

Then uncomment and set `certificate_arn` in `dev.tfvars`.

## Applying

```bash
cd terraform
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

## Production/Staging

Production and staging environments require valid ACM certificates (AWS-issued via DNS validation or imported from a CA). Do not use self-signed certificates outside of dev.
