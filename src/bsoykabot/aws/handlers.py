"""AWS Lambda entry points.

Two discovery functions and one worker function all live in this module
and share the same deployed code; Lambda is configured to call a different
top-level function in each case. The two discovery functions differ only
in which task they run -- see ``infra/lambda.tf``.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import boto3
import pywikibot
from loguru import logger

from bsoykabot.aws.metrics import emit_page_outcome, emit_pages_discovered
from bsoykabot.aws.queue import ENQUEUE_BATCH_SIZE, send_batch
from bsoykabot.tasks import draft_case, proxy_urls
from bsoykabot.wiki.editor import save_page
from bsoykabot.wiki.site import get_site

if TYPE_CHECKING:
    from bsoykabot.aws._typing import (
        BatchItemFailure,
        BatchResponse,
        DiscoverEvent,
        LambdaContext,
        SQSEvent,
    )
    from bsoykabot.tasks import Task

TASKS_BY_NAME: dict[str, Task] = {
    'proxy_urls': proxy_urls.ProxyUrlsTask(),
    'draft_case': draft_case.DraftCaseTask(),
}

# A discovery run that has self-invoked this many times stops instead of
# continuing, so a bug in a task's discover() can't turn into an infinite,
# silently self-perpetuating (and silently billed) invocation chain.
_MAX_GENERATION = 20

# Below this much remaining time, a discovery invocation stops taking new
# pages and hands off to a fresh invocation instead of risking a Lambda
# timeout mid-page.
_REMAINING_TIME_BUDGET_MS = 120_000


def discover_proxy_urls(event: DiscoverEvent, context: LambdaContext) -> None:
    """Discover pages for Task 2 and enqueue them for editing.

    Args:
        event: The invoking event -- empty on a scheduled trigger, or a
            continuation payload from a prior invocation of this same
            function.
        context: The Lambda context object.
    """
    _discover(TASKS_BY_NAME['proxy_urls'], event, context)


def discover_draft_case(event: DiscoverEvent, context: LambdaContext) -> None:
    """Discover pages for Task 3 and enqueue them for editing.

    Args:
        event: The invoking event -- empty on a scheduled trigger, or a
            continuation payload from a prior invocation of this same
            function.
        context: The Lambda context object.
    """
    _discover(TASKS_BY_NAME['draft_case'], event, context)


def _discover(task: Task, event: DiscoverEvent, context: LambdaContext) -> None:
    """Run one task's discovery phase, enqueuing pages as they're found.

    If the invocation's remaining time drops below
    _REMAINING_TIME_BUDGET_MS before discovery finishes, this function
    asynchronously re-invokes itself with a continuation payload carrying
    the discovery cursor, so one full discovery run can span more than one
    Lambda invocation without ever risking a mid-page timeout.

    Args:
        task: The task whose discover() method to run.
        event: The invoking event.
        context: The Lambda context object.

    Raises:
        RuntimeError: If the continuation chain has already reached
            _MAX_GENERATION invocations.
    """
    generation = event.get('generation', 0)
    if generation >= _MAX_GENERATION:
        msg = f'Discovery for {task.name} exceeded {_MAX_GENERATION} continuations.'
        raise RuntimeError(msg)

    max_discover = _max_discover()
    enqueued_total = event.get('enqueued_total', 0)
    enqueued_this_invocation = 0
    queue_url = os.environ['BSOYKABOT_QUEUE_URL']
    sqs = boto3.client('sqs')

    titles: list[str] = []
    resume_cursor: str | None = None

    for discovered in task.discover(cursor=event.get('cursor')):
        if max_discover is not None and enqueued_total >= max_discover:
            logger.info(f'Reached BSOYKABOT_MAX_DISCOVER={max_discover}; stopping.')
            if titles:
                send_batch(sqs, queue_url, task_name=task.name, titles=titles)
            emit_pages_discovered(task.name, enqueued_this_invocation)
            return

        titles.append(discovered.title)
        resume_cursor = discovered.cursor
        enqueued_total += 1
        enqueued_this_invocation += 1

        if len(titles) == ENQUEUE_BATCH_SIZE:
            send_batch(sqs, queue_url, task_name=task.name, titles=titles)
            titles = []

        if context.get_remaining_time_in_millis() < _REMAINING_TIME_BUDGET_MS:
            if titles:
                send_batch(sqs, queue_url, task_name=task.name, titles=titles)

            _continue_later(
                context,
                cursor=resume_cursor,
                generation=generation + 1,
                enqueued_total=enqueued_total,
            )
            emit_pages_discovered(task.name, enqueued_this_invocation)
            return

    if titles:
        send_batch(sqs, queue_url, task_name=task.name, titles=titles)

    emit_pages_discovered(task.name, enqueued_this_invocation)
    logger.info(f'Finished discovery for {task.name}: enqueued {enqueued_total} pages.')


def _continue_later(
    context: LambdaContext,
    *,
    cursor: str | None,
    generation: int,
    enqueued_total: int,
) -> None:
    """Asynchronously re-invoke the current discovery function to continue.

    Args:
        context: The Lambda context object, whose invoked_function_arn
            names the function to re-invoke -- itself.
        cursor: The discovery cursor to resume from.
        generation: How many continuations have happened so far, including
            this one.
        enqueued_total: How many pages have been enqueued so far, so
            BSOYKABOT_MAX_DISCOVER stays accurate across continuations.
    """
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=context.invoked_function_arn,
        InvocationType='Event',
        Payload=json.dumps(
            {
                'cursor': cursor,
                'generation': generation,
                'enqueued_total': enqueued_total,
            },
        ).encode('utf-8'),
    )
    logger.info(f'Continuing discovery in a new invocation (generation {generation}).')


def _max_discover() -> int | None:
    """Read the BSOYKABOT_MAX_DISCOVER cap, if one is configured.

    Returns:
        The maximum number of pages to enqueue in one full discovery run,
        across any continuations, or None for no limit.
    """
    raw = os.environ.get('BSOYKABOT_MAX_DISCOVER')
    return int(raw) if raw else None


def process(event: SQSEvent, context: LambdaContext) -> BatchResponse:
    """Process a batch of pages from SQS.

    A single bad page must not fail the eight or nine good ones batched
    alongside it, and the range of exceptions the MediaWiki API and
    mwparserfromhell can raise isn't practical to enumerate -- so failures
    here are caught broadly, logged with a traceback, and reported back to
    Lambda individually via the partial-batch-failure response, which
    redelivers only the pages that actually failed.

    Args:
        event: The SQS event containing page records.
        context: The Lambda context object.

    Returns:
        The identifiers of any messages that should be retried.
    """
    del context

    site = get_site()
    failures: list[BatchItemFailure] = []

    for record in event['Records']:
        message = json.loads(record['body'])
        task = TASKS_BY_NAME[message['task']]
        page = pywikibot.Page(site, message['title'])

        try:
            text = task.handle(page)
            if text is None:
                emit_page_outcome(task.name, 'no_change')
            elif save_page(page, text, task=task):
                emit_page_outcome(task.name, 'edited')
            else:
                emit_page_outcome(task.name, 'blocked')
        except Exception:  # noqa: BLE001 -- see the docstring above
            logger.exception(f'Failed to process {message["title"]!r} ({task.name})')
            emit_page_outcome(task.name, 'error')
            failures.append({'itemIdentifier': record['messageId']})

    return {'batchItemFailures': failures}
