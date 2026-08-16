"""SQS helpers shared by the discovery Lambda functions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from mypy_boto3_sqs.client import SQSClient
    from mypy_boto3_sqs.type_defs import SendMessageBatchRequestEntryTypeDef

ENQUEUE_BATCH_SIZE = 10


def send_batch(
    sqs: SQSClient,
    queue_url: str,
    *,
    task_name: str,
    titles: list[str],
) -> None:
    """Send up to ENQUEUE_BATCH_SIZE page titles to SQS as one batch.

    Args:
        sqs: A boto3 SQS client.
        queue_url: The queue to send to.
        task_name: The task these titles belong to, carried in each
            message body so the shared worker function can dispatch each
            message to the right task.
        titles: The page titles to enqueue. Must be no more than
            ENQUEUE_BATCH_SIZE long, since that's SendMessageBatch's own
            per-request limit.
    """
    entries: list[SendMessageBatchRequestEntryTypeDef] = [
        {
            'Id': str(index),
            'MessageBody': json.dumps({'task': task_name, 'title': title}),
        }
        for index, title in enumerate(titles)
    ]

    response = sqs.send_message_batch(QueueUrl=queue_url, Entries=entries)

    for failure in response.get('Failed', []):
        logger.warning(
            f'Failed to enqueue message {failure["Id"]}: {failure["Message"]}',
        )
