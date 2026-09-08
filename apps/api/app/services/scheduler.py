import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.services.job_monitor import monitor_jobs


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_monitoring_job():
    """
    Run one JobForge monitoring cycle.

    A fresh database session is created for every
    execution and closed afterward.
    """

    db = SessionLocal()

    try:
        result = monitor_jobs(db=db)

        logger.info(
            "Job monitoring completed: %s",
            result,
        )

    except Exception:
        logger.exception(
            "Job monitoring failed"
        )

    finally:
        db.close()


def start_scheduler():
    """
    Start the JobForge background scheduler.
    """

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

    # Run the first monitoring cycle immediately.
    run_monitoring_job()


def stop_scheduler():
    """
    Stop the JobForge background scheduler.
    """

    if not scheduler.running:
        return

    scheduler.shutdown(
        wait=False
    )

    logger.info(
        "JobForge scheduler stopped."
    )