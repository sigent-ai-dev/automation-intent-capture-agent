resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project_name}-${var.environment}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "record_type"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "record_type"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "last_activity"
    type = "N"
  }

  attribute {
    name = "user_email"
    type = "S"
  }

  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "last_activity"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "user-email-index"
    hash_key        = "user_email"
    range_key       = "last_activity"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
