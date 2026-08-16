variable "project_name" {
  type        = string
  default     = "wikipedia-bot"
  description = "Project name."
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region."
}

variable "put_throttle_seconds" {
  type        = number
  default     = 10
  description = "Seconds Pywikibot waits between saves within one worker invocation."
}

variable "max_discover_draft_case" {
  type        = number
  default     = 1000
  description = <<-EOT
    Maximum pages a single draft_case discovery run (across any
    self-invoked continuations) will enqueue, reproducing the previous
    PAGES_PER_BATCH cap so this task's on-wiki edit rate doesn't change as
    part of this migration. proxy_urls had no equivalent cap before this
    migration and gets none now.
  EOT
}

variable "simulate" {
  type        = bool
  default     = true
  description = <<-EOT
    Whether the worker blocks every save via Pywikibot's simulate mode
    instead of actually editing. Starts true so the whole pipeline can be
    validated against live Wikipedia with zero edits; flipped to false,
    one task at a time, once that validation has passed.
  EOT
}

variable "schedules_enabled" {
  type        = bool
  default     = false
  description = <<-EOT
    Whether the EventBridge schedules are enabled. Starts false so the
    pipeline can be exercised with manual invocations before it runs
    unattended.
  EOT
}

variable "log_retention_days" {
  type        = number
  default     = 14
  description = "CloudWatch Logs retention for all three Lambda functions."
}

variable "alert_email" {
  type        = string
  description = "Email address subscribed to the bsoykabot-alerts SNS topic."
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags."
}
