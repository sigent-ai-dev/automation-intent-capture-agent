# Quickstart: Vite 6 Upgrade and Cognito Authentication

## Prerequisites

- Node.js 20+
- npm 10+
- AWS account with Cognito configured (or use `terraform apply` from `terraform/`)
- Cognito user pool ID and client ID

## Environment Variables

Create `frontend/.env.local`:

```env
VITE_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_COGNITO_DOMAIN=intent-capture-dev-123456789.auth.us-east-1.amazoncognito.com
VITE_COGNITO_REDIRECT_URI=http://localhost:5173
VITE_ENABLE_FEDERATION=false
```

## Development

```bash
cd frontend
npm install
npm run dev
```

The app will start at http://localhost:5173. Without valid Cognito config, the app logs a console warning and shows the login form (which will fail auth attempts gracefully).

## Running Tests

```bash
npm test              # unit tests (vitest)
npm run test:e2e      # e2e tests (playwright)
npm run type-check    # TypeScript check
```

## Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

The cognito module outputs `user_pool_id` and `client_id` for use in the frontend env vars.

## Creating a Test User

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <POOL_ID> \
  --username test@example.com \
  --temporary-password TempPass1! \
  --user-attributes Name=email,Value=test@example.com

aws cognito-idp admin-add-user-to-group \
  --user-pool-id <POOL_ID> \
  --username test@example.com \
  --group-name admin
```

First login will prompt for a new password (NewPasswordForm).

## Verifying Auth Flow

1. Open http://localhost:5173 → see LoginForm
2. Enter credentials → redirected to voice interface
3. Check browser DevTools Network tab → WebSocket upgrade includes `Sec-WebSocket-Protocol` header with token
4. Click Sign Out → returned to LoginForm
