# With Sentry removed, these alarms are the only signal that anything is
# wrong -- CloudWatch Logs still holds the tracebacks, but nothing pages
# without an alarm watching for them.

resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"

  tags = var.tags
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "proxy_urls_dlq_depth" {
  alarm_name          = "${local.name_prefix}-proxy-urls-dlq-depth"
  alarm_description   = "A proxy_urls page failed 5 times and landed in the DLQ."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.proxy_urls_dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "draft_case_dlq_depth" {
  alarm_name          = "${local.name_prefix}-draft-case-dlq-depth"
  alarm_description   = "A draft_case page failed 5 times and landed in the DLQ."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.draft_case_dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "discover_proxy_urls_errors" {
  alarm_name          = "${local.name_prefix}-discover-proxy-urls-errors"
  alarm_description   = "Task 2 discovery raised an error."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.discover_proxy_urls.function_name }
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "discover_draft_case_errors" {
  alarm_name          = "${local.name_prefix}-discover-draft-case-errors"
  alarm_description   = "Task 3 discovery raised an error."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.discover_draft_case.function_name }
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "worker_errors" {
  alarm_name          = "${local.name_prefix}-worker-errors"
  alarm_description   = "The worker raised 5+ errors in 15 minutes (sustained breakage, not one bad page)."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.worker.function_name }
  statistic           = "Sum"
  period              = 900
  evaluation_periods  = 1
  threshold           = 5
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# The most valuable alarm here: today's code swallows OtherPageSaveError
# and just logs a warning, so a bug that makes every single save throw it
# would produce a bot that runs cleanly, errors zero times, and edits
# nothing. Only queue age catches "the worker is running but not draining."

resource "aws_cloudwatch_metric_alarm" "proxy_urls_queue_stalled" {
  alarm_name          = "${local.name_prefix}-proxy-urls-queue-stalled"
  alarm_description   = "proxy_urls messages have been sitting unprocessed for over a day."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateAgeOfOldestMessage"
  dimensions          = { QueueName = aws_sqs_queue.proxy_urls.name }
  statistic           = "Maximum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 86400
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "draft_case_queue_stalled" {
  alarm_name          = "${local.name_prefix}-draft-case-queue-stalled"
  alarm_description   = "draft_case messages have been sitting unprocessed for over a day."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateAgeOfOldestMessage"
  dimensions          = { QueueName = aws_sqs_queue.draft_case.name }
  statistic           = "Maximum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 86400
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}
