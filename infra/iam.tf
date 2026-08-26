# Lambda execution roles

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

# The parameter is a SecureString encrypted with the account's default SSM
# key, so decrypting it on read needs kms:Decrypt on that key in addition to
# ssm:GetParameter -- the key's own policy allowing the account isn't enough,
# each role's identity policy must grant it too.
data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

# Every function bootstraps Pywikibot's credentials from Parameter Store at
# cold start (see bsoykabot.wiki._bootstrap), so all three roles need read
# access to the one parameter regardless of what else they do.
data "aws_iam_policy_document" "read_wikipedia_credentials" {
  statement {
    sid    = "AllowReadWikipediaCredentials"
    effect = "Allow"

    actions = ["ssm:GetParameter"]

    resources = [aws_ssm_parameter.wikipedia.arn]
  }

  statement {
    sid    = "AllowDecryptWithSsmKey"
    effect = "Allow"

    actions = ["kms:Decrypt"]

    resources = [data.aws_kms_alias.ssm.target_key_arn]
  }
}

# discover-proxy-urls

resource "aws_iam_role" "discover_proxy_urls" {
  name               = "${local.name_prefix}-discover-proxy-urls"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "discover_proxy_urls_basic_execution" {
  role       = aws_iam_role.discover_proxy_urls.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "discover_proxy_urls_read_credentials" {
  name   = "read-wikipedia-credentials"
  role   = aws_iam_role.discover_proxy_urls.id
  policy = data.aws_iam_policy_document.read_wikipedia_credentials.json
}

data "aws_iam_policy_document" "discover_proxy_urls" {
  statement {
    sid    = "AllowEnqueueProxyUrlsPages"
    effect = "Allow"

    actions = ["sqs:SendMessage", "sqs:SendMessageBatch"]

    resources = [aws_sqs_queue.proxy_urls.arn]
  }

  statement {
    sid    = "AllowSelfInvokeForContinuation"
    effect = "Allow"

    actions = ["lambda:InvokeFunction"]

    # Constructed from parts, not aws_lambda_function.discover_proxy_urls.arn,
    # to avoid a Terraform dependency cycle between this function and the
    # execution role its own definition depends on.
    resources = ["arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}-discover-proxy-urls"]
  }
}

resource "aws_iam_role_policy" "discover_proxy_urls" {
  name   = "discover-proxy-urls"
  role   = aws_iam_role.discover_proxy_urls.id
  policy = data.aws_iam_policy_document.discover_proxy_urls.json
}

# discover-draft-case

resource "aws_iam_role" "discover_draft_case" {
  name               = "${local.name_prefix}-discover-draft-case"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "discover_draft_case_basic_execution" {
  role       = aws_iam_role.discover_draft_case.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "discover_draft_case_read_credentials" {
  name   = "read-wikipedia-credentials"
  role   = aws_iam_role.discover_draft_case.id
  policy = data.aws_iam_policy_document.read_wikipedia_credentials.json
}

data "aws_iam_policy_document" "discover_draft_case" {
  statement {
    sid    = "AllowEnqueueDraftCasePages"
    effect = "Allow"

    actions = ["sqs:SendMessage", "sqs:SendMessageBatch"]

    resources = [aws_sqs_queue.draft_case.arn]
  }

  statement {
    sid    = "AllowSelfInvokeForContinuation"
    effect = "Allow"

    actions = ["lambda:InvokeFunction"]

    resources = ["arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}-discover-draft-case"]
  }
}

resource "aws_iam_role_policy" "discover_draft_case" {
  name   = "discover-draft-case"
  role   = aws_iam_role.discover_draft_case.id
  policy = data.aws_iam_policy_document.discover_draft_case.json
}

# worker

resource "aws_iam_role" "worker" {
  name               = "${local.name_prefix}-worker"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "worker_basic_execution" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "worker_read_credentials" {
  name   = "read-wikipedia-credentials"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.read_wikipedia_credentials.json
}

data "aws_iam_policy_document" "worker" {
  statement {
    sid    = "AllowConsumeBothQueues"
    effect = "Allow"

    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]

    resources = [
      aws_sqs_queue.proxy_urls.arn,
      aws_sqs_queue.draft_case.arn,
    ]
  }
}

resource "aws_iam_role_policy" "worker" {
  name   = "worker"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker.json
}

# EventBridge Scheduler

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    effect = "Allow"

    principals {
      identifiers = ["scheduler.amazonaws.com"]
      type        = "Service"
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${local.name_prefix}-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json

  tags = local.common_tags
}

data "aws_iam_policy_document" "scheduler" {
  statement {
    sid    = "AllowInvokeDiscoveryFunctions"
    effect = "Allow"

    actions = ["lambda:InvokeFunction"]

    resources = [
      aws_lambda_function.discover_proxy_urls.arn,
      aws_lambda_function.discover_draft_case.arn,
    ]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "scheduler"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler.json
}
