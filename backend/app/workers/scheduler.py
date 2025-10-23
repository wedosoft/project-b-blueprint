"""APScheduler bootstrap utilities for background tasks."""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.config import get_settings

logger = logging.getLogger(__name__)

SchedulerType = AsyncIOScheduler

_scheduler: SchedulerType | None = None
_scheduler_lock = asyncio.Lock()


async def ensure_scheduler() -> SchedulerType | None:
    """Create and start the global scheduler if enabled.

    Returns the running scheduler instance, or ``None`` when disabled.
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    async with _scheduler_lock:
        if _scheduler and _scheduler.running:
            return _scheduler

        settings = get_settings()
        if not settings.backend.scheduler_enabled:
            logger.info("Scheduler disabled via settings.")
            return None

        scheduler = AsyncIOScheduler(timezone="UTC")
        _register_default_jobs(scheduler)
        scheduler.start()
        _scheduler = scheduler
        logger.info("APScheduler started with %d jobs.", len(scheduler.get_jobs()))
        return _scheduler


async def shutdown_scheduler(wait: bool = True) -> None:
    """Shut down the scheduler if it is running."""
    global _scheduler
    if not _scheduler:
        return
    async with _scheduler_lock:
        if _scheduler and _scheduler.running:
            logger.info("Stopping APScheduler...")
            _scheduler.shutdown(wait=wait)
        _scheduler = None


def _register_default_jobs(scheduler: SchedulerType) -> None:
    """Register baseline jobs required for MVP reliability."""
    scheduler.add_job(
        monitor_approval_timeouts,
        trigger=IntervalTrigger(seconds=60),
        id="approval_timeout_scan",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )


async def monitor_approval_timeouts() -> None:
    """Placeholder job for approval timeout handling (implemented in US2)."""
    logger.debug("Approval timeout scan tick (stub).")


__all__ = [
    "ensure_scheduler",
    "shutdown_scheduler",
    "monitor_approval_timeouts",
]
