import logging
import os
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.services.digest_service import process_digest_notifications
from app.services.job_monitor import monitor_jobs
from app.services.digest_service import process_immediate_notifications


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    timezone=ZoneInfo("Africa/Lagos")
)


def get_digest_schedule() -> tuple[int, int]:
    """
    Read and validate the daily digest schedule from environment variables.

    Defaults to 08:00 if the configured hour or minute is invalid.
    """

    default_hour = 8
    default_minute = 0

    try:
        hour = int(os.getenv("DIGEST_HOUR", str(default_hour)))
        minute = int(os.getenv("DIGEST_MINUTE", str(default_minute)))
    except ValueError:
        logger.warning(
            "Invalid digest schedule configuration. "
            "Falling back to 08:00."
        )
        return default_hour, default_minute

    if not 0 <= hour <= 23:
        logger.warning(
            "Invalid DIGEST_HOUR=%s. Falling back to 08:00.",
            hour,
        )
        return default_hour, default_minute

    if not 0 <= minute <= 59:
        logger.warning(
            "Invalid DIGEST_MINUTE=%s. Falling back to 08:00.",
            minute,
        )
        return default_hour, default_minute

    return hour, minute


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
        result = process_digest_notifications(db=db)

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
    )

    if digest_enabled:
        scheduler.add_job(
            run_digest_job,
            trigger="cron",
            hour=digest_hour,
            minute=digest_minute,
            id="jobforge_daily_digest",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )

        logger.info(
            "Daily digest scheduled for %02d:%02d",
            digest_hour,
            digest_minute,
        )
    else:
        logger.info(
            "Daily digest is disabled."
        )

    scheduler.start()

    logger.info(
        "JobForge scheduler started. "
        "Monitoring every 15 minutes."
    )

    run_monitoring_job()


def stop_scheduler():
    if not scheduler.running:
        return

    scheduler.shutdown(wait=False)

    logger.info(
        "JobForge scheduler stopped."
    )