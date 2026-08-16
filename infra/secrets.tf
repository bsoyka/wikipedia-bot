resource "aws_secretsmanager_secret" "wikipedia" {
  name = "${var.project_name}/prod/external/wikipedia"

  tags = var.tags
}

# The secret's value is managed out-of-band, not through Terraform -- see
# infra/README.md for how to generate and set it. This keeps the bot
# password out of tfvars and Terraform state. Its shape:
#   {"username": "BsoykaBot", "bot_name": "lambda", "bot_password": "..."}
