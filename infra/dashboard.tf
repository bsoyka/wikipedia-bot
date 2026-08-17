# One dashboard covering both halves of what can go wrong: infrastructure
# health (is anything running, is anything stuck or failing) and bot
# activity (is the bot actually finding and fixing pages). The alarms in
# monitoring.tf catch the former; this dashboard makes both visible without
# waiting for an alarm to fire.

locals {
  dashboard_body = jsonencode({
    widgets = [
      {
        type       = "text"
        x          = 0, y = 0, width = 24, height = 1
        properties = { markdown = "## Infrastructure health" }
      },

      # Lambda invocations, errors, and duration across all three
      # functions -- the first place to look for "is anything running."
      {
        type = "metric"
        x    = 0, y = 1, width = 8, height = 6
        properties = {
          title  = "Invocations"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Sum"
          metrics = [for name, label in local.function_labels :
            ["AWS/Lambda", "Invocations", "FunctionName", name, { label = label }]
          ]
        }
      },
      {
        type = "metric"
        x    = 8, y = 1, width = 8, height = 6
        properties = {
          title  = "Errors"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Sum"
          metrics = [for name, label in local.function_labels :
            ["AWS/Lambda", "Errors", "FunctionName", name, { label = label }]
          ]
        }
      },
      {
        type = "metric"
        x    = 16, y = 1, width = 8, height = 6
        properties = {
          title  = "Duration (p90)"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "p90"
          metrics = [for name, label in local.function_labels :
            ["AWS/Lambda", "Duration", "FunctionName", name, { label = label }]
          ]
        }
      },

      # Queue depth and age -- age is the important one: it's what catches
      # a bug that makes every save silently no-op, since that produces
      # zero errors anywhere else on this dashboard.
      {
        type = "metric"
        x    = 0, y = 7, width = 12, height = 6
        properties = {
          title  = "Queue depth"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Maximum"
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.proxy_urls.name, { label = "proxy_urls" }],
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.draft_case.name, { label = "draft_case" }],
          ]
        }
      },
      {
        type = "metric"
        x    = 12, y = 7, width = 12, height = 6
        properties = {
          title  = "Oldest message age"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Maximum"
          metrics = [
            ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", aws_sqs_queue.proxy_urls.name, { label = "proxy_urls" }],
            ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", aws_sqs_queue.draft_case.name, { label = "draft_case" }],
          ]
        }
      },

      {
        type = "metric"
        x    = 0, y = 13, width = 12, height = 6
        properties = {
          title  = "Dead-letter queue depth"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          stat   = "Maximum"
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.proxy_urls_dlq.name, { label = "proxy_urls" }],
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", aws_sqs_queue.draft_case_dlq.name, { label = "draft_case" }],
          ]
        }
      },
      {
        type = "alarm"
        x    = 12, y = 13, width = 12, height = 6
        properties = {
          title = "Alarm status"
          alarms = [
            aws_cloudwatch_metric_alarm.proxy_urls_dlq_depth.arn,
            aws_cloudwatch_metric_alarm.draft_case_dlq_depth.arn,
            aws_cloudwatch_metric_alarm.discover_proxy_urls_errors.arn,
            aws_cloudwatch_metric_alarm.discover_draft_case_errors.arn,
            aws_cloudwatch_metric_alarm.worker_errors.arn,
            aws_cloudwatch_metric_alarm.proxy_urls_queue_stalled.arn,
            aws_cloudwatch_metric_alarm.draft_case_queue_stalled.arn,
          ]
        }
      },

      {
        type       = "text"
        x          = 0, y = 19, width = 24, height = 1
        properties = { markdown = "## Bot activity" }
      },

      # Custom metrics from bsoykabot.aws.metrics (namespace "BsoykaBot",
      # dimensioned by Task). These only exist once the worker and
      # discovery functions have actually run at least once each --
      # they won't appear in the metric picker until then.
      {
        type = "metric"
        x    = 0, y = 20, width = 8, height = 6
        properties = {
          title  = "Pages edited"
          view   = "timeSeries"
          region = var.aws_region
          period = 86400
          stat   = "Sum"
          metrics = [
            ["BsoykaBot", "PagesEdited", "Task", "proxy_urls"],
            ["BsoykaBot", "PagesEdited", "Task", "draft_case"],
          ]
        }
      },
      {
        type = "metric"
        x    = 8, y = 20, width = 8, height = 6
        properties = {
          title  = "Pages discovered"
          view   = "timeSeries"
          region = var.aws_region
          period = 86400
          stat   = "Sum"
          metrics = [
            ["BsoykaBot", "PagesDiscovered", "Task", "proxy_urls"],
            ["BsoykaBot", "PagesDiscovered", "Task", "draft_case"],
          ]
        }
      },
      {
        type = "metric"
        x    = 16, y = 20, width = 8, height = 6
        properties = {
          title  = "Pages skipped, blocked, or errored"
          view   = "timeSeries"
          region = var.aws_region
          period = 86400
          stat   = "Sum"
          metrics = [
            ["BsoykaBot", "PagesNoChange", "Task", "proxy_urls", { label = "proxy_urls: no change" }],
            ["BsoykaBot", "PagesNoChange", "Task", "draft_case", { label = "draft_case: no change" }],
            ["BsoykaBot", "PagesBlocked", "Task", "proxy_urls", { label = "proxy_urls: blocked" }],
            ["BsoykaBot", "PagesBlocked", "Task", "draft_case", { label = "draft_case: blocked" }],
            ["BsoykaBot", "PagesError", "Task", "proxy_urls", { label = "proxy_urls: error" }],
            ["BsoykaBot", "PagesError", "Task", "draft_case", { label = "draft_case: error" }],
          ]
        }
      },
    ]
  })

  function_labels = {
    (aws_lambda_function.discover_proxy_urls.function_name) = "discover: proxy_urls"
    (aws_lambda_function.discover_draft_case.function_name) = "discover: draft_case"
    (aws_lambda_function.worker.function_name)              = "worker"
  }
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = local.name_prefix
  dashboard_body = local.dashboard_body
}
