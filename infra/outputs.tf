output "wikipedia_secret_arn" {
  value       = aws_secretsmanager_secret.wikipedia.arn
  description = "ARN of the Secrets Manager secret holding the bot's Wikipedia credentials -- set its value out-of-band, see infra/README.md."
}

output "discover_proxy_urls_function_name" {
  value       = aws_lambda_function.discover_proxy_urls.function_name
  description = "Name of the Task 2 discovery function, for manual invocation."
}

output "discover_draft_case_function_name" {
  value       = aws_lambda_function.discover_draft_case.function_name
  description = "Name of the Task 3 discovery function, for manual invocation."
}

output "worker_function_name" {
  value       = aws_lambda_function.worker.function_name
  description = "Name of the shared worker function."
}
