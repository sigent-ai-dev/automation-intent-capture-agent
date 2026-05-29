bucket         = "intent-capture-tfstate"
key            = "infra/terraform.tfstate"
region         = "eu-west-1"
dynamodb_table = "intent-capture-tfstate-lock"
encrypt        = true
