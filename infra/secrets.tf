resource "aws_ssm_parameter" "wikipedia" {
  name = "/${var.project_name}/prod/external/wikipedia"
  type = "SecureString"

  # The real value is managed out-of-band, not through Terraform -- see
  # infra/README.md for how to generate and set it. This keeps the bot
  # password out of tfvars and Terraform state. Its shape:
  #   {"username": "BsoykaBot", "bot_name": "lambda", "bot_password": "..."}
  value = "unset"

  lifecycle {
    ignore_changes = [value]
  }

  tags = var.tags
}
