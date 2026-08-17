"""Custom CloudWatch metrics for bot activity, via the Embedded Metric Format.

EMF metrics are extracted from ordinary CloudWatch Logs lines: CloudWatch
scans each log event for a specially-shaped JSON document and turns it into
real metric data points, with no ``cloudwatch:PutMetricData`` call, no
extra IAM permission beyond the log-write access every Lambda function
already has, and no added latency.

This has to go through a raw ``print`` to stdout rather than loguru: EMF
requires the log line to be *exactly* the JSON document below, and loguru's
default formatting (timestamps, level tags, color codes) would corrupt it.
"""

from __future__ import annotations

import json
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal

    PageOutcome = Literal['edited', 'no_change', 'blocked', 'error']

_NAMESPACE = 'BsoykaBot'


def emit_page_outcome(task_name: str, outcome: PageOutcome) -> None:
    """Record one page's handling outcome as a CloudWatch metric.

    Args:
        task_name: The task that processed the page ('proxy_urls' or
            'draft_case'), recorded as a dimension so each task's rate can
            be graphed separately.
        outcome: What happened to the page -- 'edited' if a save
            succeeded, 'no_change' if handle() found nothing to fix,
            'blocked' if a change was computed but the save permanently
            failed (e.g. page protection), or 'error' if an exception
            propagated and the message will be retried.
    """
    _emit(
        task_name,
        {
            'PagesEdited': 1 if outcome == 'edited' else 0,
            'PagesNoChange': 1 if outcome == 'no_change' else 0,
            'PagesBlocked': 1 if outcome == 'blocked' else 0,
            'PagesError': 1 if outcome == 'error' else 0,
        },
    )


def emit_pages_discovered(task_name: str, count: int) -> None:
    """Record how many pages one discovery invocation enqueued.

    Args:
        task_name: The task whose discovery enqueued these pages.
        count: How many pages this invocation enqueued. When discovery
            spans multiple self-invoked continuations, each invocation
            reports only its own share -- CloudWatch's own Sum statistic
            adds them back up over a dashboard's time range, so reporting
            the running total here would double-count.
    """
    _emit(task_name, {'PagesDiscovered': count})


def _emit(task_name: str, metrics: dict[str, int]) -> None:
    """Write one Embedded Metric Format log line.

    Args:
        task_name: Recorded as the 'Task' dimension.
        metrics: Metric name to value, each counted with unit 'Count'.
    """
    document = {
        '_aws': {
            'Timestamp': int(time.time() * 1000),
            'CloudWatchMetrics': [
                {
                    'Namespace': _NAMESPACE,
                    'Dimensions': [['Task']],
                    'Metrics': [{'Name': name, 'Unit': 'Count'} for name in metrics],
                },
            ],
        },
        'Task': task_name,
        **metrics,
    }
    print(json.dumps(document), file=sys.stdout)  # noqa: T201 -- EMF needs raw stdout
