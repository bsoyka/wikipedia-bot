resource "aws_lambda_layer_version" "dependencies" {
  layer_name       = "${local.name_prefix}-dependencies"
  filename         = data.archive_file.layer.output_path
  source_code_hash = data.archive_file.layer.output_base64sha256

  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["arm64"]
}

locals {
  # Every function bootstraps Pywikibot from the same credentials and needs
  # the same base configuration; only the queue URL (and, for discovery
  # functions, the enqueue cap) differs.
  common_environment = {
    HOME                         = "/tmp"
    PYWIKIBOT_DIR                = "/tmp/pywikibot"
    BSOYKABOT_CREDENTIALS_SECRET = aws_secretsmanager_secret.wikipedia.name
    BSOYKABOT_PUT_THROTTLE       = tostring(var.put_throttle_seconds)
    BSOYKABOT_SIMULATE           = var.simulate ? "1" : "0"
    BSOYKABOT_LOG_LEVEL          = "INFO"
  }
}

resource "aws_cloudwatch_log_group" "discover_proxy_urls" {
  name              = "/aws/lambda/${local.name_prefix}-discover-proxy-urls"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "discover_draft_case" {
  name              = "/aws/lambda/${local.name_prefix}-discover-draft-case"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${local.name_prefix}-worker"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_lambda_function" "discover_proxy_urls" {
  function_name = "${local.name_prefix}-discover-proxy-urls"
  role          = aws_iam_role.discover_proxy_urls.arn
  handler       = "bsoykabot.aws.handlers.discover_proxy_urls"
  runtime       = "python3.13"
  architectures = ["arm64"]

  # Task 2's insource: search is well within CirrusSearch's paging limits
  # today, so this is generous headroom rather than an expected duration.
  timeout     = 900
  memory_size = 512

  filename         = data.archive_file.code.output_path
  source_code_hash = data.archive_file.code.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  # The only rate governor left once Pywikibot's cross-process throttle
  # stops working on Lambda's ephemeral /tmp -- see bsoykabot.wiki.site.
  reserved_concurrent_executions = 1

  environment {
    variables = merge(local.common_environment, {
      # No BSOYKABOT_MAX_DISCOVER: see max_discover_draft_case's
      # description in variables.tf for why this task doesn't need one.
      BSOYKABOT_QUEUE_URL = aws_sqs_queue.proxy_urls.url
    })
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [aws_cloudwatch_log_group.discover_proxy_urls]

  tags = var.tags
}

resource "aws_lambda_function" "discover_draft_case" {
  function_name = "${local.name_prefix}-discover-draft-case"
  role          = aws_iam_role.discover_draft_case.arn
  handler       = "bsoykabot.aws.handlers.discover_draft_case"
  runtime       = "python3.13"
  architectures = ["arm64"]

  # Task 3's discovery calls Site.backlinks() on ~90+ redirect titles and
  # can plausibly run past 15 minutes on a large wiki; the handler
  # self-invokes with a continuation payload before that happens (see
  # bsoykabot.aws.handlers._discover), so this timeout bounds one
  # invocation's slice of the work, not the whole discovery run.
  timeout     = 900
  memory_size = 1024

  filename         = data.archive_file.code.output_path
  source_code_hash = data.archive_file.code.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  reserved_concurrent_executions = 1

  environment {
    variables = merge(local.common_environment, {
      BSOYKABOT_QUEUE_URL    = aws_sqs_queue.draft_case.url
      BSOYKABOT_MAX_DISCOVER = tostring(var.max_discover_draft_case)
    })
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [aws_cloudwatch_log_group.discover_draft_case]

  tags = var.tags
}

resource "aws_lambda_function" "worker" {
  function_name = "${local.name_prefix}-worker"
  role          = aws_iam_role.worker.arn
  handler       = "bsoykabot.aws.handlers.process"
  runtime       = "python3.13"
  architectures = ["arm64"]

  timeout     = 300
  memory_size = 512

  filename         = data.archive_file.code.output_path
  source_code_hash = data.archive_file.code.output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  # Serializes every edit the bot makes, globally. Composes with
  # BSOYKABOT_PUT_THROTTLE for an exact, calculable edit-rate ceiling
  # (1 / put_throttle_seconds), and eliminates edit conflicts between the
  # two tasks touching the same page concurrently. See bsoykabot.wiki.site
  # for the full argument.
  reserved_concurrent_executions = 1

  environment {
    variables = local.common_environment
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [aws_cloudwatch_log_group.worker]

  tags = var.tags
}
