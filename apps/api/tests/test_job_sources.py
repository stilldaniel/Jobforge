from unittest.mock import Mock, patch

import pytest

from app.job_sources.arbeitnow import ArbeitnowJobSource
from app.job_sources.common import html_to_text, normalize_salary
from app.job_sources.company_boards import (
    AshbyJobSource,
    GreenhouseJobSource,
    LeverJobSource,
)
from app.job_sources.himalayas import HimalayasJobSource
from app.job_sources.jobicy import JobicyJobSource
from app.job_sources.registry import get_job_sources
from app.job_sources.remoteok import RemoteOKJobSource
from app.job_sources.remotive import RemotiveJobSource
from app.job_sources.weworkremotely import WeWorkRemotelyJobSource


def mock_json(payload):
    response = Mock()
    response.json.return_value = payload
    response.text = payload if isinstance(payload, str) else ""
    return response


def patch_get(*payloads):
    return patch(
        "app.job_sources.common.httpx.get",
        side_effect=[mock_json(payload) for payload in payloads],
    )


# ============================================================
# HELPERS
# ============================================================

def test_html_to_text_keeps_paragraphs_and_lists():
    text = html_to_text(
        "<h2>About</h2><p>We build&nbsp;apps.</p>"
        "<ul><li>React</li><li>TypeScript</li></ul>"
    )

    assert text == "About\nWe build apps.\n• React\n• TypeScript"


def test_html_to_text_handles_escaped_html():
    assert html_to_text("&lt;p&gt;Hello&lt;/p&gt;") == "Hello"


def test_html_to_text_handles_empty_values():
    assert html_to_text(None) is None
    assert html_to_text("") is None


def test_normalize_salary_converts_monthly_to_yearly():
    assert normalize_salary(1000, 2000, "usd", "monthly") == (
        12000,
        24000,
        "USD",
        "year",
    )


def test_normalize_salary_requires_currency_and_period():
    assert normalize_salary(1000, 2000, None, "yearly") == (
        None,
        None,
        None,
        None,
    )
    assert normalize_salary(1000, 2000, "USD", None) == (
        None,
        None,
        None,
        None,
    )


def test_normalize_salary_treats_zero_as_missing():
    assert normalize_salary(0, 0, "USD", "year") == (
        None,
        None,
        None,
        None,
    )


# ============================================================
# SOURCES
# ============================================================

def test_remotive_searches_each_query():
    payload = {
        "jobs": [
            {
                "url": "https://remotive.com/remote-jobs/1",
                "title": "Frontend Developer",
                "company_name": "Acme ",
                "description": "<p>React</p>",
                "candidate_required_location": "Worldwide",
                "publication_date": "2026-10-02T20:01:00",
            }
        ]
    }

    source = RemotiveJobSource()
    source.search_queries = ["frontend developer", "react developer"]

    with patch_get(payload, payload) as mock_get:
        jobs = source.fetch_jobs()

    assert mock_get.call_count == 2
    assert mock_get.call_args_list[0].kwargs["params"]["search"] == (
        "frontend developer"
    )

    job = jobs[0]
    assert job.company == "Acme"
    assert job.description == "React"
    assert job.remote_eligibility == "Worldwide"
    assert job.work_type == "remote"
    assert job.source == "remotive"
    assert job.posted_at.tzinfo is not None


def test_remoteok_skips_legal_notice_and_maps_salary():
    payload = [
        {"legal": "Terms"},
        {
            "position": "React Engineer",
            "company": "Bjak",
            "description": "<p>Build things</p>",
            "location": "Singapore",
            "salary_min": 80000,
            "salary_max": 0,
            "url": "https://remoteok.com/remote-jobs/1",
            "date": "2026-09-23T00:00:04+00:00",
        },
    ]

    with patch_get(payload):
        jobs = RemoteOKJobSource().fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].remote_eligibility == "Singapore"
    assert jobs[0].salary_min == 80000
    assert jobs[0].salary_max is None
    assert jobs[0].salary_currency == "USD"
    assert jobs[0].salary_period == "year"


def test_arbeitnow_maps_remote_flag():
    payload = {
        "data": [
            {
                "title": "Backend Engineer",
                "company_name": "Wolt",
                "description": "<p>Go</p>",
                "remote": True,
                "url": "https://www.arbeitnow.com/jobs/1",
                "location": "Berlin, Germany",
                "created_at": 1791269131,
            },
            {
                "title": "Office Manager",
                "company_name": "Wolt",
                "remote": False,
                "url": "https://www.arbeitnow.com/jobs/2",
                "location": "Berlin, Germany",
            },
        ]
    }

    with patch_get(payload):
        jobs = ArbeitnowJobSource().fetch_jobs()

    assert jobs[0].work_type == "remote"
    assert jobs[0].location == "Berlin, Germany"
    assert jobs[1].work_type is None


def test_jobicy_maps_geo_and_salary():
    payload = {
        "jobs": [
            {
                "url": "https://jobicy.com/jobs/1",
                "jobTitle": "Support Engineer",
                "companyName": "Roboflow",
                "jobGeo": "USA",
                "jobDescription": "<p>Help customers</p>",
                "salaryMin": 5000,
                "salaryMax": 6000,
                "salaryCurrency": "USD",
                "salaryPeriod": "monthly",
                "pubDate": "2026-10-06T04:50:06+00:00",
            }
        ]
    }

    with patch_get(payload):
        jobs = JobicyJobSource().fetch_jobs()

    assert jobs[0].remote_eligibility == "USA"
    assert jobs[0].salary_min == 60000
    assert jobs[0].salary_max == 72000


def test_himalayas_uses_search_and_location_restrictions():
    payload = {
        "jobs": [
            {
                "title": "React Developer",
                "companyName": "Acme",
                "description": "<p>React</p>",
                "locationRestrictions": ["Nigeria", "Ghana"],
                "minSalary": 40000,
                "maxSalary": 60000,
                "currency": "USD",
                "salaryPeriod": "annual",
                "applicationLink": "https://himalayas.app/jobs/1",
                "pubDate": 1791271727,
            },
            {
                "title": "Frontend Developer",
                "companyName": "Beta",
                "locationRestrictions": [],
                "guid": "https://himalayas.app/jobs/2",
            },
        ]
    }

    source = HimalayasJobSource()
    source.search_queries = ["react developer"]

    with patch_get(payload) as mock_get:
        jobs = source.fetch_jobs()

    assert mock_get.call_args.args[0] == HimalayasJobSource.SEARCH_URL
    assert jobs[0].remote_eligibility == "Nigeria, Ghana"
    assert jobs[0].salary_min == 40000
    assert jobs[1].remote_eligibility == "Worldwide"
    assert jobs[1].application_url == "https://himalayas.app/jobs/2"


def test_weworkremotely_parses_rss():
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
      <item>
        <title>Sezzle: Frontend Engineer</title>
        <region>Anywhere in the World</region>
        <country>🇲🇽 Mexico</country>
        <description>&lt;p&gt;Build UI&lt;/p&gt;</description>
        <pubDate>Tue, 06 Oct 2026 07:31:26 +0000</pubDate>
        <link>https://weworkremotely.com/remote-jobs/1</link>
      </item>
      <item>
        <title>No Company Separator</title>
        <country>🇲🇽 Mexico</country>
        <link>https://weworkremotely.com/remote-jobs/2</link>
      </item>
    </channel></rss>"""

    with patch_get(feed):
        jobs = WeWorkRemotelyJobSource().fetch_jobs()

    assert jobs[0].company == "Sezzle"
    assert jobs[0].title == "Frontend Engineer"
    assert jobs[0].remote_eligibility == "Anywhere in the World"
    assert jobs[0].description == "Build UI"
    assert jobs[1].company == "Unknown Company"
    assert jobs[1].remote_eligibility == "Mexico"


def test_greenhouse_marks_remote_locations():
    payload = {
        "jobs": [
            {
                "absolute_url": "https://stripe.com/jobs/1",
                "title": "Frontend Engineer",
                "company_name": "Stripe",
                "location": {"name": "Remote - US"},
                "content": "&lt;p&gt;Payments&lt;/p&gt;",
                "first_published": "2026-09-03T13:30:34-04:00",
            },
            {
                "absolute_url": "https://stripe.com/jobs/2",
                "title": "Designer",
                "location": {"name": "Dublin"},
            },
        ]
    }

    with patch_get(payload):
        jobs = GreenhouseJobSource(boards=["stripe"]).fetch_jobs()

    assert jobs[0].work_type == "remote"
    assert jobs[0].remote_eligibility == "Remote - US"
    assert jobs[0].description == "Payments"
    assert jobs[1].work_type is None
    assert jobs[1].company == "Stripe"


def test_company_board_skips_failing_board():
    good = [
        {
            "hostedUrl": "https://jobs.lever.co/spotify/1",
            "text": "Android Engineer",
            "categories": {"location": "London"},
            "workplaceType": "hybrid",
            "createdAt": 1782214185805,
        }
    ]

    failing = Mock()
    failing.raise_for_status.side_effect = RuntimeError("404")

    with patch(
        "app.job_sources.common.httpx.get",
        side_effect=[failing, mock_json(good)],
    ):
        jobs = LeverJobSource(boards=["gone", "spotify"]).fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].company == "Spotify"
    assert jobs[0].work_type == "hybrid"


def test_company_board_raises_when_every_board_fails():
    failing = Mock()
    failing.raise_for_status.side_effect = RuntimeError("404")

    with patch(
        "app.job_sources.common.httpx.get",
        return_value=failing,
    ):
        with pytest.raises(RuntimeError, match="All boards failed"):
            LeverJobSource(boards=["gone"]).fetch_jobs()


def test_ashby_maps_remote_locations_and_compensation():
    payload = {
        "jobs": [
            {
                "title": "Security Engineer",
                "jobUrl": "https://jobs.ashbyhq.com/ramp/1",
                "location": "New York, NY",
                "secondaryLocations": [
                    {"location": "Remote (US)"},
                    {"location": "Miami, FL"},
                ],
                "isRemote": True,
                "workplaceType": "Hybrid",
                "isListed": True,
                "descriptionPlain": "Secure things",
                "publishedAt": "2026-04-07T17:12:35.753+00:00",
                "compensation": {
                    "compensationTiers": [
                        {
                            "components": [
                                {
                                    "compensationType": "EquityPercentage",
                                    "interval": "NONE",
                                },
                                {
                                    "compensationType": "Salary",
                                    "interval": "1 YEAR",
                                    "currencyCode": "USD",
                                    "minValue": 211400,
                                    "maxValue": 290600,
                                },
                            ]
                        }
                    ]
                },
            },
            {
                "title": "Hidden",
                "jobUrl": "https://jobs.ashbyhq.com/ramp/2",
                "isListed": False,
            },
        ]
    }

    with patch_get(payload):
        jobs = AshbyJobSource(boards=["ramp"]).fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].company == "Ramp"
    assert jobs[0].work_type == "hybrid"
    assert jobs[0].remote_eligibility is None
    assert jobs[0].salary_min == 211400
    assert jobs[0].salary_currency == "USD"


def test_registry_builds_every_new_source(monkeypatch):
    monkeypatch.setenv(
        "JOB_SOURCES",
        "remotive,remoteok,arbeitnow,jobicy,himalayas,"
        "weworkremotely,greenhouse,lever,ashby",
    )
    monkeypatch.setenv("GREENHOUSE_BOARDS", "stripe, airbnb")

    sources = get_job_sources()

    assert len(sources) == 9
    assert sources[6].boards == ["stripe", "airbnb"]
    assert all(source.filter_by_relevance for source in sources)
