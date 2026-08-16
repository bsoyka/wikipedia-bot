# Two work queues, not one shared queue: Task 3's weekly discovery drops
# thousands of messages at once, and with the worker's reserved concurrency
# pinned to 1 (see lambda.tf), a shared queue would let that backlog block
# Task 2's daily run for hours behind it. Separate queues also give each
# task its own retention (a rediscovered-daily queue can safely expire
# messages after a day; a rediscovered-weekly one can't), its own DLQ so a
# poison-pill page in one task doesn't block redriving the other, and a
# per-task ApproximateAgeOfOldestMessage metric, which is the best signal
# available that the bot has silently stopped working.

resource "aws_sqs_queue" "proxy_urls_dlq" {
  name                      = "${local.name_prefix}-proxy-urls-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = var.tags
}

resource "aws_sqs_queue" "proxy_urls" {
  name = "${local.name_prefix}-proxy-urls"

  # 6x the worker's function timeout, per AWS's own guidance for SQS/Lambda
  # event source mappings.
  visibility_timeout_seconds = 1800
  # This task rediscovers every page it cares about daily, so a message
  # older than a day is pure waste.
  message_retention_seconds = 86400
  receive_wait_time_seconds = 20
  sqs_managed_sse_enabled   = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.proxy_urls_dlq.arn
    # Not 1 or 2: at reserved concurrency 1, Lambda throttles the SQS
    # poller whenever the worker is already busy, which returns the batch
    # to the queue and increments its receive count same as a real
    # failure would. A low maxReceiveCount would DLQ perfectly good
    # messages for no reason other than the worker being busy.
    maxReceiveCount = 5
  })

  tags = var.tags
}

resource "aws_sqs_queue_redrive_allow_policy" "proxy_urls_dlq" {
  queue_url = aws_sqs_queue.proxy_urls_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.proxy_urls.arn]
  })
}

resource "aws_sqs_queue" "draft_case_dlq" {
  name                      = "${local.name_prefix}-draft-case-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = var.tags
}

resource "aws_sqs_queue" "draft_case" {
  name = "${local.name_prefix}-draft-case"

  visibility_timeout_seconds = 1800
  # This task only rediscovers weekly.
  message_retention_seconds = 604800
  receive_wait_time_seconds = 20
  sqs_managed_sse_enabled   = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.draft_case_dlq.arn
    maxReceiveCount     = 5
  })

  tags = var.tags
}

resource "aws_sqs_queue_redrive_allow_policy" "draft_case_dlq" {
  queue_url = aws_sqs_queue.draft_case_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.draft_case.arn]
  })
}

# One worker function, not two: reserved concurrency is a per-function
# property, so two worker functions at concurrency 1 each would give two
# uncoordinated concurrent editors, defeating the point (see lambda.tf).
# The task each message belongs to travels in the message body instead.

resource "aws_lambda_event_source_mapping" "proxy_urls" {
  event_source_arn = aws_sqs_queue.proxy_urls.arn
  function_name    = aws_lambda_function.worker.arn

  # Load-bearing, not a default: pywikibot's put_throttle only rate-limits
  # writes within one process, spacing them by put_throttle_seconds since
  # the previous save in the same invocation. A batch of 10 pages is what
  # turns that into real rate limiting instead of one 10-second sleep per
  # invocation for nothing. It also amortizes login and cold start.
  batch_size                         = 10
  maximum_batching_window_in_seconds = 30

  function_response_types = ["ReportBatchItemFailures"]
}

resource "aws_lambda_event_source_mapping" "draft_case" {
  event_source_arn = aws_sqs_queue.draft_case.arn
  function_name    = aws_lambda_function.worker.arn

  batch_size                         = 10
  maximum_batching_window_in_seconds = 30

  function_response_types = ["ReportBatchItemFailures"]
}
