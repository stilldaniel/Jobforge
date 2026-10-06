// Sample data for the public demo (NEXT_PUBLIC_DEMO_MODE=true).
// Companies, people and links are invented; scores and reasons follow
// the real matching rules so the demo shows how JobForge behaves.

import type {
  Application,
  CareerProfile,
  Job,
  MatchedJob,
  Notification,
  NotificationPreferences,
  SavedJob,
  User,
} from "@/types/api";

export const DEMO_USER_ID = 1;

function hoursAgo(hours: number): string {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

export const demoUser: User = {
  id: DEMO_USER_ID,
  email: "demo@jobforge.example",
  full_name: "Demo User",
  timezone: "Africa/Lagos",
  created_at: hoursAgo(24 * 30),
  updated_at: hoursAgo(24 * 2),
};

export const demoPreferences: NotificationPreferences = {
  job_alerts_enabled: true,
  high_match_alerts_enabled: true,
  digest_notifications_enabled: true,
  email_notifications_enabled: true,
};

export const demoProfile: CareerProfile = {
  id: 1,
  user_id: DEMO_USER_ID,
  professional_title: "Frontend Developer",
  years_of_experience: 4,
  summary:
    "Frontend developer building fast, accessible web apps with React, " +
    "Next.js and TypeScript.",
  skills: JSON.stringify([
    "React",
    "Next.js",
    "TypeScript",
    "JavaScript",
    "HTML",
    "CSS",
    "Tailwind CSS",
    "Git",
  ]),
  candidate_location: "Lagos, Nigeria",
  preferred_work_type: "remote",
  preferred_location: "Remote",
  minimum_salary: 3000,
  maximum_salary: 5000,
  salary_currency: "USD",
  salary_period: "month",
  created_at: hoursAgo(24 * 30),
  updated_at: hoursAgo(24 * 2),
};

interface DemoJob {
  title: string;
  company: string;
  source: string;
  location: string | null;
  remote_eligibility: string | null;
  work_type: string | null;
  skills: string[];
  experience: number | null;
  salary: [number, number] | null;
  posted_hours_ago: number;
  score: number;
  reasons: string[];
  description: string;
}

const JOBS: DemoJob[] = [
  {
    title: "Senior Frontend Engineer",
    company: "Northwind Labs",
    source: "himalayas",
    location: "Remote",
    remote_eligibility: "Worldwide",
    work_type: "remote",
    skills: ["React", "TypeScript", "Next.js"],
    experience: 4,
    salary: [70000, 95000],
    posted_hours_ago: 2,
    score: 97,
    reasons: [
      "Strong frontend job title match",
      "All required skills matched",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote job accepts candidates worldwide",
      "Job salary fits candidate salary preference",
    ],
    description:
      "Northwind Labs builds analytics tools used by product teams around the world.\n" +
      "You'll own our customer-facing dashboard, built with React, Next.js and TypeScript.\n" +
      "4+ years of experience building production web apps.\n" +
      "Fully remote, open to candidates anywhere.",
  },
  {
    title: "Frontend Developer",
    company: "Brightpath",
    source: "remotive",
    location: "Remote",
    remote_eligibility: "Worldwide",
    work_type: "remote",
    skills: ["React", "TypeScript", "CSS"],
    experience: null,
    salary: null,
    posted_hours_ago: 5,
    score: 94,
    reasons: [
      "Exact job title match",
      "All required skills matched",
      "No specific experience requirement",
      "Preferred work type matched",
      "Remote job accepts candidates worldwide",
      "Job salary is not specified",
    ],
    description:
      "Brightpath is an online learning platform for 2 million students.\n" +
      "Join the web team building our course player and student dashboard in React and TypeScript.\n" +
      "We care about accessibility, performance and clean CSS.",
  },
  {
    title: "React Developer",
    company: "Kora Payments",
    source: "jobicy",
    location: "Remote",
    remote_eligibility: "Africa, Europe",
    work_type: "remote",
    skills: ["React", "JavaScript", "Tailwind CSS"],
    experience: 3,
    salary: [48000, 60000],
    posted_hours_ago: 9,
    score: 92,
    reasons: [
      "Related frontend job title",
      "All required skills matched",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote job accepts candidates from candidate location",
      "Job salary fits candidate salary preference",
    ],
    description:
      "Kora Payments helps African businesses accept payments online.\n" +
      "Build our merchant dashboard with React, JavaScript and Tailwind CSS.\n" +
      "3+ years of experience. Remote across Africa and Europe.",
  },
  {
    title: "Frontend Engineer",
    company: "Lumen Health",
    source: "remoteok",
    location: "Remote",
    remote_eligibility: null,
    work_type: "remote",
    skills: ["React", "Next.js", "TypeScript"],
    experience: 3,
    salary: [80000, 110000],
    posted_hours_ago: 14,
    score: 89,
    reasons: [
      "Strong frontend job title match",
      "All required skills matched",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote eligibility is not geographically specified",
      "Job salary fits candidate salary preference",
    ],
    description:
      "Lumen Health makes appointment booking simple for clinics.\n" +
      "Help us rebuild our patient app with Next.js and TypeScript.\n" +
      "3+ years of React experience.",
  },
  {
    title: "Next.js Developer",
    company: "Atlas Commerce",
    source: "weworkremotely",
    location: "Remote",
    remote_eligibility: "Anywhere in the World",
    work_type: "remote",
    skills: ["Next.js", "React", "GraphQL"],
    experience: 5,
    salary: null,
    posted_hours_ago: 24 * 3,
    score: 84,
    reasons: [
      "Related frontend job title",
      "Most required skills matched (2/3)",
      "Candidate is one year below the experience requirement",
      "Preferred work type matched",
      "Remote job accepts candidates worldwide",
      "Job salary is not specified",
    ],
    description:
      "Atlas Commerce powers online stores for independent brands.\n" +
      "Work on our storefront framework built with Next.js, React and GraphQL.\n" +
      "5+ years of experience.",
  },
  {
    title: "UI Engineer",
    company: "Fieldnote",
    source: "himalayas",
    location: "Remote",
    remote_eligibility: "Worldwide",
    work_type: "remote",
    skills: ["TypeScript", "CSS", "Figma"],
    experience: 3,
    salary: [55000, 70000],
    posted_hours_ago: 24 * 6,
    score: 78,
    reasons: [
      "Some job title similarity",
      "Most required skills matched (2/3)",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote job accepts candidates worldwide",
      "Job salary fits candidate salary preference",
    ],
    description:
      "Fieldnote is a note-taking app for research teams.\n" +
      "Build our design system in TypeScript and CSS, working closely with designers in Figma.",
  },
  {
    title: "Full Stack Developer (React)",
    company: "Harbor Logistics",
    source: "arbeitnow",
    location: "Remote",
    remote_eligibility: "Worldwide",
    work_type: "remote",
    skills: ["React", "Node.js", "PostgreSQL", "Docker"],
    experience: 4,
    salary: null,
    posted_hours_ago: 24 * 9,
    score: 71,
    reasons: [
      "Some job title similarity",
      "Few required skills matched (1/4)",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote job accepts candidates worldwide",
      "Job salary is not specified",
    ],
    description:
      "Harbor Logistics tracks shipments for 500 freight companies.\n" +
      "Work across our React frontend and Node.js services backed by PostgreSQL.",
  },
  {
    title: "Junior Frontend Developer",
    company: "Pixel & Co",
    source: "remotive",
    location: "Remote",
    remote_eligibility: "Worldwide",
    work_type: "remote",
    skills: ["HTML", "CSS", "JavaScript"],
    experience: 1,
    salary: [24000, 30000],
    posted_hours_ago: 24 * 12,
    score: 66,
    reasons: [
      "Related frontend job title",
      "All required skills matched",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote job accepts candidates worldwide",
      "Job salary is below candidate minimum",
    ],
    description:
      "Pixel & Co is a small design studio building marketing sites.\n" +
      "A junior role writing HTML, CSS and JavaScript. Pay is shown for reference; JobForge never hides a job over pay.",
  },
  {
    title: "Frontend Developer",
    company: "Redwood Insurance",
    source: "remoteok",
    location: "Remote",
    remote_eligibility: "United States",
    work_type: "remote",
    skills: ["React", "TypeScript"],
    experience: 3,
    salary: [90000, 120000],
    posted_hours_ago: 6,
    score: 49,
    reasons: [
      "Job has an eligibility mismatch",
      "Exact job title match",
      "All required skills matched",
      "Experience requirement satisfied",
      "Preferred work type matched",
      "Remote job does not accept candidates from candidate location",
      "Job salary fits candidate salary preference",
    ],
    description:
      "A great fit on paper, but this role only hires in the United States, so JobForge caps it at 49 and never emails about it.",
  },
  {
    title: "Senior React Engineer",
    company: "Kiel Mobility",
    source: "arbeitnow",
    location: "Berlin, Germany",
    remote_eligibility: null,
    work_type: "hybrid",
    skills: ["React", "TypeScript", "Redux"],
    experience: 5,
    salary: null,
    posted_hours_ago: 18,
    score: 49,
    reasons: [
      "Job has an eligibility mismatch",
      "Strong frontend job title match",
      "Most required skills matched (2/3)",
      "Candidate is one year below the experience requirement",
      "Preferred work type does not match",
      "Job location does not match candidate location",
      "Job salary is not specified",
    ],
    description:
      "A hybrid role in Berlin, 3 days a week in the office. Ineligible for a candidate in Lagos, so it's shown but never notified.",
  },
];

function slug(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

export const demoJobs: Job[] = JOBS.map((job, index) => ({
  id: index + 1,
  title: job.title,
  company: job.company,
  description: job.description,
  required_skills: JSON.stringify(job.skills),
  required_experience: job.experience,
  location: job.location,
  remote_eligibility: job.remote_eligibility,
  work_type: job.work_type,
  salary_min: job.salary ? job.salary[0] : null,
  salary_max: job.salary ? job.salary[1] : null,
  salary_currency: job.salary ? "USD" : null,
  salary_period: job.salary ? "year" : null,
  application_url: `https://example.com/jobs/${slug(job.company)}-${slug(job.title)}`,
  source: job.source,
  fingerprint: `demo-${index + 1}`,
  posted_at: hoursAgo(job.posted_hours_ago),
  created_at: hoursAgo(job.posted_hours_ago),
  updated_at: hoursAgo(job.posted_hours_ago),
}));

export const demoMatches: MatchedJob[] = JOBS.map((job, index) => {
  const listing = demoJobs[index];

  return {
    id: index + 1,
    user_id: DEMO_USER_ID,
    job_id: listing.id,
    score: job.score,
    match_reasons: job.reasons.join("; "),
    title: listing.title,
    company: listing.company,
    description: listing.description,
    required_skills: listing.required_skills,
    required_experience: listing.required_experience,
    location: listing.location,
    remote_eligibility: listing.remote_eligibility,
    work_type: listing.work_type,
    salary_min: listing.salary_min,
    salary_max: listing.salary_max,
    salary_currency: listing.salary_currency,
    salary_period: listing.salary_period,
    application_url: listing.application_url,
    created_at: listing.created_at,
    updated_at: listing.updated_at,
  };
}).sort((a, b) => b.score - a.score);

// Matches of 89+ are emailed straight away; 60–88 go into the digest.
export const demoNotifications: Notification[] = demoMatches
  .filter((match) => match.score >= 60)
  .map((match, index) => {
    const immediate = match.score >= 89;

    return {
      id: index + 1,
      user_id: DEMO_USER_ID,
      job_match_id: match.id,
      notification_type: immediate ? "immediate" : "digest",
      channel: "email",
      status: "sent",
      title: immediate ? "New high-quality job match" : "New job match",
      message: `${match.title} at ${match.company} matches your career profile with a score of ${match.score}%.`,
      attempts: 1,
      last_error: null,
      created_at: match.created_at,
      sent_at: match.created_at,
      read_at: index < 2 ? null : match.created_at,
    };
  });

function jobById(id: number): Job {
  return demoJobs.find((job) => job.id === id) as Job;
}

export const demoSavedJobs: SavedJob[] = [3, 4].map((jobId, index) => ({
  id: index + 1,
  user_id: DEMO_USER_ID,
  job_id: jobId,
  created_at: hoursAgo(4 + index),
  job: jobById(jobId),
}));

// Applied after each job was posted (see posted_hours_ago above).
export const demoApplications: Application[] = [
  { jobId: 7, status: "interview", hours: 24 * 8, notes: "Technical interview on Thursday." },
  { jobId: 6, status: "applied", hours: 24 * 5, notes: "Sent portfolio link." },
  { jobId: 5, status: "applied", hours: 24 * 2, notes: null },
  { jobId: 2, status: "applied", hours: 3, notes: null },
  { jobId: 8, status: "rejected", hours: 24 * 10, notes: null },
].map((application, index) => ({
  id: index + 1,
  user_id: DEMO_USER_ID,
  job_id: application.jobId,
  status: application.status,
  applied_at: hoursAgo(application.hours),
  notes: application.notes,
  job: jobById(application.jobId),
}));
