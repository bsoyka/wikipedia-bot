# BsoykaBot infrastructure

BsoykaBot runs on AWS: EventBridge Scheduler triggers a discovery Lambda
function for each task, which enqueues candidate pages to SQS, which feeds a
shared worker Lambda function that computes and saves edits. See the
docstrings in [`bsoykabot.aws.handlers`](../src/bsoykabot/aws/handlers.py)
and [`bsoykabot.wiki`](../src/bsoykabot/wiki/__init__.py) for how the pieces
fit together; this document covers only how to set up and drive the
infrastructure itself.

Deploys are applied by hand from your machine, not from CI, so you'll need
your own AWS credentials configured (e.g. via `aws configure` or SSO) with
access to this account.

## One-time setup

These steps aren't managed by Terraform, so they're not repeated by
`terraform apply` -- do them once, in order, before the first apply.

### 1. Tool versions

This directory's tool versions (Terraform, uv) are pinned in
[`../mise.toml`](../mise.toml). If you use [mise](https://mise.jdx.dev/), run
`mise install` from the repo root and everything below will use the pinned
versions automatically.

### 2. `prod.tfvars`

`prod.tfvars` is gitignored, matching how this account's other Terraform
projects treat environment-specific tfvars files. Create your own at
`infra/prod.tfvars`:

```hcl
project_name = "wikipedia-bot"
aws_region   = "us-east-1"
alert_email  = "you@example.com" # subscribed to the bsoykabot-alerts SNS topic

tags = {
  Owner = "Your Name"
  Env   = "prod"
}
```

See [`variables.tf`](variables.tf) for every variable and its default.

### 3. The Wikipedia credentials secret

The bot authenticates with a
[BotPassword](https://www.mediawiki.org/wiki/Special:BotPasswords), not the
main account password, so it can be scoped and revoked independently.

1. Log in as the bot account and go to
   [Special:BotPasswords](https://en.wikipedia.org/wiki/Special:BotPasswords).
2. Create a new bot password (e.g. named `lambda`) with at least the
   `Edit existing pages` and `High-volume editing` grants. Note the
   generated password -- it's shown only once.
3. Create the secret and set its value:

   ```shell
   aws secretsmanager create-secret \
     --name wikipedia-bot/prod/external/wikipedia \
     --secret-string '{"username": "BsoykaBot", "bot_name": "lambda", "bot_password": "..."}'
   ```

   `username` is the bot's main account name; `bot_name` and `bot_password`
   are what Special:BotPasswords generated. Terraform reads this secret by
   name (`aws_secretsmanager_secret.wikipedia`) -- its value is never in
   tfvars or state.

   If you're running this alongside the bot's old SSH-server deployment
   during the migration, use a **different** bot password than the server's,
   so each can be revoked independently and the two are distinguishable in
   Wikipedia's API logs.

## Everyday commands

```shell
just build      # build the Lambda layer and code zip locally
just tf-plan     # build, then terraform plan
just tf-apply    # build, then terraform apply
```

`tf-plan` and `tf-apply` both rebuild the layer and code artifacts first, so
`source_code_hash` always reflects what's actually on disk -- Terraform will
show a real diff whenever the code changes, and no diff when it hasn't.

## Rolling out safely

The bot edits real Wikipedia articles, so bring the pipeline up in stages
rather than flipping it on all at once:

1. **Dry run.** Leave `simulate = true` (the default) and both schedules
   disabled (`proxy_urls_schedule_enabled` / `draft_case_schedule_enabled`
   = `false`, also the defaults). Apply, then invoke a discovery function
   manually:

   ```shell
   aws lambda invoke --function-name wikipedia-bot-discover-proxy-urls --payload '{}' /dev/stdout
   ```

   Watch the corresponding CloudWatch Logs group and SQS queue: pywikibot
   logs `SIMULATION: ... action blocked` for every page it would have
   edited, and the queue should drain to zero as the worker processes it. No
   edits happen -- `simulate` blocks writes but not login, so this also
   proves the credentials bootstrap works end to end.

2. **Enable writes for one task.** Set `simulate = false`, apply, and invoke
   that task's discovery function manually again. Check
   [Special:Contributions/BsoykaBot](https://en.wikipedia.org/wiki/Special:Contributions/BsoykaBot)
   for the first handful of edits before trusting it further.

3. **Enable that task's schedule.** Set `proxy_urls_schedule_enabled = true`
   (or `draft_case_schedule_enabled`) and apply. The two are independent, so
   enabling one doesn't affect the other -- but `simulate` is not: it's one
   Pywikibot session shared by the worker across both tasks' queues, so
   flipping it to `false` enables real writes for whichever task's messages
   the worker happens to pick up next, not just the one you're staging.

4. **Repeat for the other task.**

## Alarms

Subscribing to `alert_email` gets you a confirmation email from SNS the
first time you apply -- confirm it, or you won't receive alerts. See
[`monitoring.tf`](monitoring.tf) for what's covered; the queue-age alarms in
particular are the only thing that would catch a bug that makes every save
silently no-op, since Sentry isn't part of this design.

## Decommissioning the old SSH deployment

Once the AWS pipeline has run cleanly for a full cycle of both tasks (at
least one weekly `draft_case` run and a few days of daily `proxy_urls`
runs):

1. Remove the server's crontab entries.
2. Delete the `deploy` job from `.github/workflows/deploy.yml` and its
   associated secrets/vars (`SSH_HOST`, `SSH_KEY`, `SSH_USERNAME`,
   `SSH_PORT`, `BOT_DIRECTORY`, `UV_PATH`).
3. Revoke the server's bot password on Special:BotPasswords -- separately
   from the Lambda one, if you followed the advice above.
4. Decommission the server itself.
