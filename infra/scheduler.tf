# EventBridge Scheduler, not a classic EventBridge rule: per-schedule IAM
# roles, timezone-aware cron, and it doesn't consume the shared default
# event bus for what is otherwise just "run this Lambda twice a week."

resource "aws_scheduler_schedule" "discover_proxy_urls" {
  name       = "${local.name_prefix}-discover-proxy-urls"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 9 * * ? *)" # daily, 09:00 UTC
  state               = var.proxy_urls_schedule_enabled ? "ENABLED" : "DISABLED"

  target {
    arn      = aws_lambda_function.discover_proxy_urls.arn
    role_arn = aws_iam_role.scheduler.arn
    # The task's identity comes from which function this schedule targets,
    # not from the payload, so the payload is reserved entirely for the
    # continuation fields a self-invocation would populate.
    input = jsonencode({})
  }
}

resource "aws_scheduler_schedule" "discover_draft_case" {
  name       = "${local.name_prefix}-discover-draft-case"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 3 ? * SUN *)" # weekly, Sunday 03:00 UTC
  state               = var.draft_case_schedule_enabled ? "ENABLED" : "DISABLED"

  target {
    arn      = aws_lambda_function.discover_draft_case.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({})
  }
}
