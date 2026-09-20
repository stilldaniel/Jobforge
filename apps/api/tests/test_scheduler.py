import app.services.scheduler as scheduler_module


def test_start_scheduler_is_idempotent(monkeypatch):
    scheduler = scheduler_module.scheduler

    if scheduler.running:
        scheduler.shutdown(wait=False)

    monitoring_calls = []
    digest_calls = []

    def fake_monitoring_job():
        monitoring_calls.append(True)

    def fake_digest_job():
        digest_calls.append(True)

    monkeypatch.setattr(
        scheduler_module,
        "run_monitoring_job",
        fake_monitoring_job,
    )

    monkeypatch.setattr(
        scheduler_module,
        "run_digest_job",
        fake_digest_job,
    )

    monkeypatch.setenv("DIGEST_ENABLED", "true")
    monkeypatch.setenv("DIGEST_HOUR", "8")
    monkeypatch.setenv("DIGEST_MINUTE", "0")

    try:
        scheduler_module.start_scheduler()
        scheduler_module.start_scheduler()

        jobs = scheduler.get_jobs()

        job_ids = {job.id for job in jobs}

        assert "jobforge_monitor" in job_ids
        assert "jobforge_daily_digest" in job_ids

        assert len(jobs) == 2

        # start_scheduler() performs one immediate monitoring run.
        assert len(monitoring_calls) == 1

        # The digest job is scheduled but should not execute immediately.
        assert len(digest_calls) == 0

    finally:
        scheduler_module.stop_scheduler()


def test_stop_scheduler_is_safe_when_already_stopped():
    scheduler = scheduler_module.scheduler

    if scheduler.running:
        scheduler.shutdown(wait=False)

    scheduler_module.stop_scheduler()

    assert scheduler.running is False


def test_digest_can_be_disabled(monkeypatch):
    scheduler = scheduler_module.scheduler

    if scheduler.running:
        scheduler.shutdown(wait=False)

    monitoring_calls = []

    def fake_monitoring_job():
        monitoring_calls.append(True)

    monkeypatch.setattr(
        scheduler_module,
        "run_monitoring_job",
        fake_monitoring_job,
    )

    monkeypatch.setenv("DIGEST_ENABLED", "false")

    try:
        scheduler_module.start_scheduler()

        jobs = scheduler.get_jobs()
        job_ids = {job.id for job in jobs}

        assert "jobforge_monitor" in job_ids
        assert "jobforge_daily_digest" not in job_ids

        assert len(jobs) == 1

        assert len(monitoring_calls) == 1

    finally:
        scheduler_module.stop_scheduler()


def test_get_digest_schedule_valid_configuration(monkeypatch):
    monkeypatch.setenv("DIGEST_HOUR", "14")
    monkeypatch.setenv("DIGEST_MINUTE", "30")

    hour, minute = scheduler_module.get_digest_schedule()

    assert hour == 14
    assert minute == 30


def test_get_digest_schedule_invalid_hour(monkeypatch):
    monkeypatch.setenv("DIGEST_HOUR", "25")
    monkeypatch.setenv("DIGEST_MINUTE", "30")

    hour, minute = scheduler_module.get_digest_schedule()

    assert hour == 8
    assert minute == 0


def test_get_digest_schedule_invalid_minute(monkeypatch):
    monkeypatch.setenv("DIGEST_HOUR", "14")
    monkeypatch.setenv("DIGEST_MINUTE", "60")

    hour, minute = scheduler_module.get_digest_schedule()

    assert hour == 8
    assert minute == 0


def test_get_digest_schedule_non_numeric_values(monkeypatch):
    monkeypatch.setenv("DIGEST_HOUR", "invalid")
    monkeypatch.setenv("DIGEST_MINUTE", "30")

    hour, minute = scheduler_module.get_digest_schedule()

    assert hour == 8
    assert minute == 0