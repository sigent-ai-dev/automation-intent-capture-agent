# Quickstart: Deploy Voice Service Infrastructure

## Prerequisites

- Terraform 1.5+
- AWS CLI configured with `sigent+builder-Admin` profile (account 885659622434)
- Docker (for building images locally)
- OpenSSL (for self-signed cert generation)

## Initial Deployment

### 1. Generate Self-Signed Certificate (first time only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/dev-key.pem -out /tmp/dev-cert.pem \
  -subj "/CN=intent-capture-dev"

aws acm import-certificate \
  --certificate fileb:///tmp/dev-cert.pem \
  --private-key fileb:///tmp/dev-key.pem \
  --region eu-west-1 \
  --profile sigent+builder-Admin \
  --query 'CertificateArn' --output text
```

Save the ARN for `terraform.tfvars`.

### 2. Provision Infrastructure

```bash
cd terraform
cp environments/dev.tfvars terraform.tfvars
# Edit terraform.tfvars with certificate_arn from step 1

terraform init
terraform plan
terraform apply
```

### 3. Push First Image

```bash
# Login to ECR
aws ecr get-login-password --region eu-west-1 --profile sigent+builder-Admin | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.eu-west-1.amazonaws.com

# Build and push
docker build -t intent-capture-voice-server:latest .
docker tag intent-capture-voice-server:latest <ecr_uri>:latest
docker push <ecr_uri>:latest
```

### 4. Verify Deployment

```bash
# Get ALB URL from terraform output
ALB_URL=$(terraform output -raw service_url)

# Health check
curl -k https://$ALB_URL/health/live
curl -k https://$ALB_URL/health/ready
```

Note: `-k` flag skips certificate verification (self-signed cert in dev).

### 5. Update Frontend

Update `frontend/.env.local`:
```env
VITE_WEBSOCKET_URL=wss://<ALB_URL>/ws/audio
VITE_API_URL=https://<ALB_URL>
```

### 6. Run Smoke Tests

```bash
SERVICE_URL=https://$ALB_URL .github/scripts/smoke-test.sh
```

## CI/CD Setup

### Configure GitHub OIDC

1. Terraform creates the OIDC provider and deploy role automatically
2. Add the role ARN as a GitHub repository secret: `AWS_DEPLOY_ROLE_ARN`
3. Trigger the deploy workflow manually or push a tag

## Testing Voice Locally

Voice requires Nova Sonic (Bedrock) access. To test voice locally:

```bash
# Run with LOCAL_MODE=false and AWS credentials
LOCAL_MODE=false AWS_PROFILE=sigent+builder-Admin uv run uvicorn voice_server.main:app --port 8080
```

With `LOCAL_MODE=true` (the default for local dev), the audio bridge is **not created** — audio is accepted but no agent response is generated. You'll see a log: `voice_disabled_local_mode`.

For pipeline testing without Bedrock, use the deployed environment (ALB) which has full Nova Sonic access.

## Troubleshooting

- **Container won't start**: Check CloudWatch logs at `/ecs/intent-capture-dev`
- **Health check failing**: Verify security group allows ALB → container on port 8080
- **WebSocket 4001**: Check Cognito env vars are set in task definition (`COGNITO_USER_POOL_ID`, `COGNITO_REGION`)
- **JWKS fetch timeout**: Verify NAT Gateway is routing egress from private subnet
- **No voice response locally**: You're likely in LOCAL_MODE=true. Run with LOCAL_MODE=false + AWS creds
- **Audio garbled/fast**: Check OUTPUT_SAMPLE_RATE matches Nova Sonic output (should be 16000)
