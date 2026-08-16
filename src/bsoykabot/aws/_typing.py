"""Shared typing helpers for the AWS Lambda entry points."""

from __future__ import annotations

from typing import Protocol, TypedDict


class LambdaContext(Protocol):
    """The subset of the Lambda context object this package uses."""

    invoked_function_arn: str

    def get_remaining_time_in_millis(self) -> int:
        """Return milliseconds left before the invocation times out."""
        ...  # pragma: no cover


class DiscoverEvent(TypedDict, total=False):
    """The event passed to a discovery function.

    Empty on the initial, schedule-triggered invocation. Populated with a
    continuation payload on any subsequent self-invocation triggered when
    an invocation is running out of time -- see
    ``bsoykabot.aws.handlers._continue_later``.
    """

    cursor: str | None
    generation: int
    enqueued_total: int


class SQSRecord(TypedDict):
    """The subset of an SQS record's fields this package uses."""

    messageId: str
    body: str


class SQSEvent(TypedDict):
    """The event Lambda passes to an SQS-triggered function."""

    Records: list[SQSRecord]


class BatchItemFailure(TypedDict):
    """One failed message identifier, per Lambda's partial-batch-failure contract."""

    itemIdentifier: str


class BatchResponse(TypedDict):
    """The value Lambda expects back for partial batch failure reporting."""

    batchItemFailures: list[BatchItemFailure]
