import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.services.digest_service import (
    get_digest_schedule,
    process_digest_notifications,
    process_immediate_notifications,
)
from app.services.job_monitor import monitor_jobs


logger = logging.getLogger(__name__)

# Jobs run on UTC; the digest is timed per user in their own timezone.
scheduler = BackgroundScheduler(
    timezone=ZoneInfo("UTC")
)


def run_monitoring_job():
    db = SessionLocal()

    try:
        result = monitor_jobs(db=db)

        logger.info(
            "Job monitoring completed: %s",
            result,
        )

        notification_result = process_immediate_notifications(
            db=db
        )

        logger.info(
            "Immediate notification processing completed: %s",
            notification_result,
        )

    except Exception:
        logger.exception(
            "Job monitoring or immediate notification processing failed"
        )

    finally:
        db.close()


def run_digest_job():
    db = SessionLocal()

    try:
        result = process_digest_notifications(
            db=db,
            only_due=True,
        )

        logger.info(
            "Daily digest processing completed: %s",
            result,
        )

    except Exception:
        logger.exception(
            "Daily digest processing failed"
        )

    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return

    digest_enabled = (
        os.getenv("DIGEST_ENABLED", "true").lower()
        == "true"
    )

    digest_hour, digest_minute = get_digest_schedule()

    scheduler.add_job(
        run_monitoring_job,
        trigger="interval",
        minutes=15,
        id="jobforge_monitor",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
        # First run starts right away, in the scheduler's background
        # thread, so a slow fetch doesn't delay API startup.
        next_run_time=datetime.now(scheduler.timezone),
    )

    if digest_enabled:
        # Check every 15 minutes which users have reached their digest
        # time locally. Quarter-hour checks cover every UTC offset,
        # including half- and quarter-hour ones (India, Nepal).
        scheduler.add_job(
            run_digest_job,
            trigger="cron",
            minute="0,15,30,45",
            id="jobforge_daily_digest",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )

        logger.info(
            "Daily digest scheduled for %02d:%02d in each user's timezone",
            digest_hour,
            digest_minute,
        )
    else:
        logger.info(
            "Daily digest is disabled."
        )

    # A scheduler that was shut down keeps its stopped thread pool,
    # which can't run jobs. Drop it so start() creates a fresh one.
    try:
        scheduler.remove_executor("default", shutdown=False)
    except KeyError:
        pass

    scheduler.start()

    logger.info(
        "JobForge scheduler started. "
        "Monitoring every 15 minutes."
    )


def stop_scheduler():
    if not scheduler.running:
        return

    scheduler.shutdown(wait=False)

    logger.info(
        "JobForge scheduler stopped."
    )