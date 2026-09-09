from datetime import datetime, timezone

from app.job_sources.base import DiscoveredJob, JobSource


class MockJobSource(JobSource):

    def fetch_jobs(self) -> list[DiscoveredJob]:
        return [
            # --------------------------------------------------
            # 1. REMOTE — WORLDWIDE
            # Expected: Location match for a candidate in Nigeria
            # --------------------------------------------------
            DiscoveredJob(
                title="Senior Frontend Developer",
                company="TechFlow",
                description=(
                    "We are looking for a senior frontend developer "
                    "with 4+ years of experience building modern web "
                    "applications. Strong experience with React, "
                    "TypeScript, Next.js, JavaScript, Git and Tailwind CSS "
                    "is required."
                ),
                location="Remote",
                remote_eligibility="Worldwide",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/senior-frontend-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 2. REMOTE — WORLDWIDE
            # Expected: Location match
            # --------------------------------------------------
            DiscoveredJob(
                title="React Developer",
                company="CloudWorks",
                description=(
                    "Build modern web applications using React, "
                    "TypeScript and modern frontend technologies. "
                    "Requires 1+ year of experience with React and "
                    "JavaScript. Experience with Git and HTML is preferred."
                ),
                location="Remote",
                remote_eligibility="Worldwide",
                work_type="remote",
                salary_min=2500,
                salary_max=4500,
                application_url=(
                    "https://example.com/jobs/react-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 3. REMOTE — WORLDWIDE
            # Expected: Location match
            # --------------------------------------------------
            DiscoveredJob(
                title="Frontend Developer",
                company="Example Technologies",
                description=(
                    "We are looking for a frontend developer with "
                    "2+ years of experience. Experience with React, "
                    "TypeScript, JavaScript, HTML, CSS and Git is required."
                ),
                location="Worldwide",
                remote_eligibility="Worldwide",
                work_type="remote",
                salary_min=2000,
                salary_max=3500,
                application_url=(
                    "https://example.com/jobs/frontend-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 4. REMOTE — UNITED STATES ONLY
            # Expected: Location mismatch for candidate in Nigeria
            # --------------------------------------------------
            DiscoveredJob(
                title="Remote Frontend Engineer",
                company="US Tech",
                description=(
                    "We are looking for a frontend engineer with "
                    "2+ years of experience. Experience with React, "
                    "TypeScript and JavaScript is required."
                ),
                location="Remote",
                remote_eligibility="United States",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/us-frontend-engineer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 5. REMOTE — NIGERIA ONLY
            # Expected: Location match for candidate in Nigeria
            # --------------------------------------------------
            DiscoveredJob(
                title="Frontend Developer Nigeria",
                company="Naija Digital",
                description=(
                    "Frontend developer required to build modern "
                    "web applications using React and TypeScript. "
                    "Requires 2+ years of experience."
                ),
                location="Remote",
                remote_eligibility="Nigeria",
                work_type="remote",
                salary_min=2500,
                salary_max=4000,
                application_url=(
                    "https://example.com/jobs/nigeria-frontend-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 6. REMOTE — UNKNOWN ELIGIBILITY
            # Expected: Unknown location eligibility, 0 location points
            # --------------------------------------------------
            DiscoveredJob(
                title="Remote JavaScript Developer",
                company="Unknown Remote Co",
                description=(
                    "Looking for a JavaScript developer with "
                    "2+ years of experience. React, TypeScript and "
                    "Git experience are required."
                ),
                location="Remote",
                remote_eligibility=None,
                work_type="remote",
                salary_min=2800,
                salary_max=4500,
                application_url=(
                    "https://example.com/jobs/remote-javascript-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 7. ON-SITE — NIGERIA
            # Expected: Location match for candidate in Nigeria
            # --------------------------------------------------
            DiscoveredJob(
                title="Frontend Engineer",
                company="Lagos Software Labs",
                description=(
                    "Frontend engineer needed to build web applications "
                    "using React, TypeScript and JavaScript. "
                    "Requires 2+ years of experience."
                ),
                location="Lagos, Nigeria",
                remote_eligibility=None,
                work_type="on-site",
                salary_min=2500,
                salary_max=4000,
                application_url=(
                    "https://example.com/jobs/lagos-frontend-engineer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 8. ON-SITE — UNITED KINGDOM
            # Expected: Location mismatch for candidate in Nigeria
            # --------------------------------------------------
            DiscoveredJob(
                title="Frontend Developer",
                company="London Digital",
                description=(
                    "Frontend developer needed with experience in "
                    "React, TypeScript, JavaScript and Git. "
                    "Requires 2+ years of experience."
                ),
                location="London, United Kingdom",
                remote_eligibility=None,
                work_type="on-site",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/london-frontend-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 9. REMOTE — WORLDWIDE
            # Expected: New job → match → notification
            # --------------------------------------------------
            DiscoveredJob(
                title="Senior React Engineer",
                company="NextGen Systems",
                description=(
                    "We are looking for a senior React engineer "
                    "with 4+ years of experience building modern "
                    "web applications. Strong experience with React, "
                    "TypeScript, Next.js, JavaScript and Git is required."
                ),
                location="Remote",
                remote_eligibility="Worldwide",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/senior-react-engineer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 10. REMOTE — WORLDWIDE
            # Expected: New job → high match → immediate notification
            # --------------------------------------------------
            DiscoveredJob(
                title="Senior Next.js Developer",
                company="FutureStack",
                description=(
                    "We are looking for a senior Next.js developer "
                    "with 4+ years of experience building modern web "
                    "applications. Strong experience with React, "
                    "Next.js, TypeScript, JavaScript, Git and "
                    "Tailwind CSS is required."
                ),
                location="Remote",
                remote_eligibility="Worldwide",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/senior-nextjs-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),

            # --------------------------------------------------
            # 11. TEST JOB — REMOTE — WORLDWIDE
            # Expected:
            # New job → match → score >90 → immediate notification
            # --------------------------------------------------
            DiscoveredJob(
                title="Frontend Developer",
                company="NotifyTest Labs",
                description=(
                    "We are looking for a frontend developer with "
                    "4+ years of experience building modern web "
                    "applications. Strong experience with React, "
                    "Next.js, TypeScript, JavaScript, HTML, CSS, "
                    "Tailwind CSS and Git is required."
                ),
                location="Remote",
                remote_eligibility="Worldwide",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/notify-test-frontend"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),
        ]