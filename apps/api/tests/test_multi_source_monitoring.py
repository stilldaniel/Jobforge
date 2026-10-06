from types import SimpleNamespace

import pytest

from app.job_sources.base import DiscoveredJob, JobSource
from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.services import job_monitor
from app.services.job_fingerprint import generate_dedupe_key
from app.services.job_ingestion import ingest_jobs
from app.services.job_monitor import monitor_jobs
from app.services.matching import calculate_match_score
from app.services.search_criteria import build_search_criteria, is_relevant


@pytest.fixture(autouse=True)
def reset_fetch_times():
    job_monitor._last_fetched_at.clear()
    yield
    job_monitor._last_fetched_at.clear()


def make_job(
    title="Frontend Developer",
    company="Acme",
    url="https://example.com/jobs/1",
    source="remotive",
    **overrides,
):
    data = dict(
        title=title,
        company=company,
        description="React and TypeScript, 2+ years of experience.",
        location="Remote",
        work_type="remote",
        salary_min=None,
        salary_max=None,
        application_url=url,
        source=source,
        posted_at=None,
        remote_eligibility="Worldwide",
    )
    data.update(overrides)
    return DiscoveredJob(**data)


class FeedSource(JobSource):
    filter_by_relevance = True

    def __init__(self, jobs):
        self.jobs = jobs
        self.calls = 0
        self.queries_seen = None

    def fetch_jobs(self):
        self.calls += 1
        self.queries_seen = list(self.search_queries)
        return self.jobs


class SlowFeedSource(FeedSource):
    min_interval_minutes = 360


def add_profile(db, user_id=1, **overrides):
    data = dict(
        user_id=user_id,
        professional_title="Frontend Developer",
        skills='["React", "TypeScript"]',
        years_of_experience=3,
        candidate_location="Lagos, Nigeria",
        preferred_work_type="remote",
    )
    data.update(overrides)
    db.add(CareerProfile(**data))
    db.flush()


# ============================================================
# DEDUPLICATION
# ============================================================

def test_dedupe_key_ignores_platform_noise():
    assert generate_dedupe_key(
        "Senior Frontend Engineer (Remote)",
        "Stripe, Inc.",
    ) == generate_dedupe_key(
        "Senior Frontend Engineer - Remote",
        "Stripe",
    )


def test_same_job_from_another_platform_is_skipped(db):
    first = FeedSource([make_job(source="remotive")])
    second = FeedSource(
        [
            make_job(
                title="Frontend Developer (Remote)",
                company="Acme Inc.",
                url="https://other.example.com/9",
                source="himalayas",
            )
        ]
    )

    first_result = ingest_jobs(db, first)
    second_result = ingest_jobs(db, second)

    assert len(first_result.created_jobs) == 1
    assert len(second_result.created_jobs) == 0
    assert second_result.duplicate_jobs == 1
    assert db.query(Job).count() == 1


def test_same_title_twice_on_one_platform_is_kept(db):
    source = FeedSource(
        [
            make_job(url="https://example.com/jobs/lagos"),
            make_job(url="https://example.com/jobs/london"),
        ]
    )

    result = ingest_jobs(db, source)

    assert len(result.created_jobs) == 2


def test_repeated_listing_in_one_batch_is_stored_once(db):
    source = FeedSource([make_job(), make_job()])

    result = ingest_jobs(db, source)

    assert len(result.created_jobs) == 1
    assert db.query(Job).count() == 1


# ============================================================
# SEARCH CRITERIA
# ============================================================

def test_search_criteria_from_profiles():
    criteria = build_search_criteria(
        [
            SimpleNamespace(
                professional_title="Senior Front-End Developer",
                skills='["React", "Tailwind CSS"]',
            ),
            SimpleNamespace(
                professional_title="Data Analyst",
                skills="SQL, Excel",
            ),
        ]
    )

    assert criteria.queries == [
        "senior front end developer",
        "data analyst",
    ]

    def relevant(title):
        return is_relevant(SimpleNamespace(title=title), criteria)

    assert relevant("Frontend Engineer")
    assert relevant("React Native Developer")
    assert relevant("Tailwind CSS Specialist")
    assert relevant("Senior Data Analyst")
    assert not relevant("Account Executive")
    assert not relevant("Backend Developer")


# ============================================================
# MONITORING
# ============================================================

def test_monitor_filters_feeds_and_passes_queries(db):
    add_profile(db)

    source = FeedSource(
        [
            make_job(title="Frontend Developer"),
            make_job(
                title="Account Executive",
                url="https://example.com/jobs/2",
            ),
        ]
    )

    result = monitor_jobs(db, sources=[source])

    assert source.queries_seen == ["frontend developer"]
    assert result["new_jobs"] == 1
    assert result["irrelevant_jobs"] == 1
    assert db.query(Job).count() == 1


def test_monitor_skips_feeds_when_there_are_no_profiles(db):
    source = FeedSource([make_job()])

    result = monitor_jobs(db, sources=[source])

    assert source.calls == 0
    assert result["sources_skipped"] == ["FeedSource"]


def test_monitor_respects_source_minimum_interval(db):
    add_profile(db)

    source = SlowFeedSource([make_job()])

    monitor_jobs(db, sources=[source])
    second_result = monitor_jobs(db, sources=[source])

    assert source.calls == 1
    assert second_result["sources_skipped"] == ["SlowFeedSource"]


def test_monitor_reports_cross_platform_duplicates(db):
    add_profile(db)

    sources = [
        FeedSource([make_job(source="remotive")]),
        FeedSource(
            [
                make_job(
                    url="https://other.example.com/1",
                    source="jobicy",
                )
            ]
        ),
    ]

    result = monitor_jobs(db, sources=sources)

    assert result["new_jobs"] == 1
    assert result["duplicate_jobs"] == 1
    assert result["matches_created"] == 1


# ============================================================
# SALARY
# ============================================================

def test_salary_with_currency_is_not_compared_to_profile():
    profile = SimpleNamespace(
        professional_title="Frontend Developer",
        skills="React",
        years_of_experience=3,
        candidate_location="Lagos, Nigeria",
        preferred_location=None,
        preferred_work_type="remote",
        minimum_salary=3000,
        maximum_salary=5000,
    )
    job = SimpleNamespace(
        title="Frontend Developer",
        required_skills='["React"]',
        required_experience=2,
        location="Remote",
        remote_eligibility="Worldwide",
        work_type="remote",
        salary_min=150000,
        salary_max=200000,
        salary_currency="USD",
        salary_period="year",
    )

    _, reasons = calculate_match_score(profile, job)

    assert (
        "Job salary could not be compared with your preference"
        in reasons
    )



# ============================================================
# ADZUNA
# ============================================================

def test_listing_with_changing_tracking_url_is_not_duplicated(db):
    first = FeedSource(
        [
            make_job(
                url="https://www.adzuna.co.uk/jobs/land/ad/1?se=AAA",
                source="adzuna",
                external_id="1",
            )
        ]
    )
    second = FeedSource(
        [
            make_job(
                url="https://www.adzuna.co.uk/jobs/land/ad/1?se=BBB",
                source="adzuna",
                external_id="1",
            )
        ]
    )

    ingest_jobs(db, first)
    result = ingest_jobs(db, second)

    assert result.created_jobs == []
    assert len(result.updated_jobs) == 1
    assert db.query(Job).count() == 1
    assert db.query(Job).one().application_url.endswith("se=BBB")


def test_uk_hybrid_job_is_ineligible_for_candidate_in_lagos():
    profile = SimpleNamespace(
        professional_title="Frontend Developer",
        skills='["React", "TypeScript"]',
        years_of_experience=3,
        candidate_location="Lagos, Nigeria",
        preferred_location=None,
        preferred_work_type="remote",
        minimum_salary=None,
        maximum_salary=None,
    )

    hybrid = SimpleNamespace(
        title="Frontend Developer",
        required_skills='["React", "TypeScript"]',
        required_experience=None,
        location="Rusholme, Manchester",
        remote_eligibility=None,
        work_type="hybrid",
        salary_min=40000,
        salary_max=50000,
        salary_currency="GBP",
        salary_period="year",
    )

    uk_remote = SimpleNamespace(
        **{
            **vars(hybrid),
            "work_type": "remote",
            "remote_eligibility": "United Kingdom",
        }
    )

    for job in (hybrid, uk_remote):
        score, reasons = calculate_match_score(profile, job)

        assert score <= 49
        assert reasons[0] == "Job has an eligibility mismatch"
