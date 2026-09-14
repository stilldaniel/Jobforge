import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.services.digest_service import (
    process_immediate_notifications,
)
from app.services.job_monitor import monitor_jobs


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_monitoring_job():
    db = SessionLocal()

    try:
        result = monitor_jobs(
            db=db,
        )

        logger.info(
            "Job monitoring completed: %s",
            result,
        )

        notification_result = process_immediate_notifications(
            db=db,
        )

        logger.info(
            "Immediate notification processing completed: %s",
            notification_result,
        )

    except Exception:
        logger.exception(
            "Job monitoring or notification processing failed"
        )

    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        run_monitoring_job,
        trigger="interval",
        minutes=15,
        id="jobforge_monitor",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
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

    scheduler.shutdown(
        wait=False,
    )

    logger.info(
        "JobForge scheduler stopped."
    )