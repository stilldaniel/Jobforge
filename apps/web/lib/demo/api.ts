// In-browser stand-in for the JobForge API, used when
// NEXT_PUBLIC_DEMO_MODE=true (the public portfolio demo). It answers the
// same paths as the real backend from sample data in ./data. Changes last
// for the browser session only.

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

import {
  DEMO_USER_ID,
  demoApplications,
  demoJobs,
  demoMatches,
  demoNotifications,
  demoPreferences,
  demoProfile,
  demoSavedJobs,
  demoUser,
} from "./data";

interface DemoState {
  user: User;
  preferences: NotificationPreferences;
  profile: CareerProfile;
  jobs: Job[];
  matches: MatchedJob[];
  notifications: Notification[];
  savedJobs: SavedJob[];
  applications: Application[];
}

const STORAGE_KEY = "jobforge-demo-state";

function initialState(): DemoState {
  // Copies, so the sample data itself is never changed.
  return JSON.parse(
    JSON.stringify({
      user: demoUser,
      preferences: demoPreferences,
      profile: demoProfile,
      jobs: demoJobs,
      matches: demoMatches,
      notifications: demoNotifications,
      savedJobs: demoSavedJobs,
      applications: demoApplications,
    }),
  );
}

let state: DemoState | null = null;

function getState(): DemoState {
  if (state) {
    return state;
  }

  try {
    const saved = window.sessionStorage.getItem(STORAGE_KEY);
    state = saved ? (JSON.parse(saved) as DemoState) : initialState();
  } catch {
    state = initialState();
  }

  return state;
}

function save(): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage can be unavailable (private mode); the demo still works
    // until the page is reloaded.
  }
}

function now(): string {
  return new Date().toISOString();
}

function nextId(items: { id: number }[]): number {
  return items.reduce((max, item) => Math.max(max, item.id), 0) + 1;
}

function notFound(what: string): never {
  throw new Error(`${what} not found`);
}

function findJob(jobId: number): Job {
  return (
    getState().jobs.find((job) => job.id === jobId) ?? notFound("Job")
  );
}

type Handler = (
  params: number[],
  body: Record<string, unknown>,
) => unknown;

const routes: [string, RegExp, Handler][] = [
  // ---------------------------------------------------------- users
  ["GET", /^\/users\/(\d+)\/notification-preferences$/, () =>
    getState().preferences],

  ["PATCH", /^\/users\/(\d+)\/notification-preferences$/, (_, body) => {
    const current = getState();
    current.preferences = { ...current.preferences, ...body };
    save();
    return current.preferences;
  }],

  ["GET", /^\/users\/(\d+)\/career-profile\/?$/, () => getState().profile],

  ["POST", /^\/users\/(\d+)\/career-profile\/?$/, (_, body) => {
    const current = getState();
    current.profile = { ...current.profile, ...body, updated_at: now() };
    save();
    return current.profile;
  }],

  ["PUT", /^\/users\/(\d+)\/career-profile\/?$/, (_, body) => {
    const current = getState();
    current.profile = { ...current.profile, ...body, updated_at: now() };
    save();
    return current.profile;
  }],

  ["GET", /^\/users\/?$/, () => [getState().user]],

  ["GET", /^\/users\/(\d+)$/, () => getState().user],

  ["PUT", /^\/users\/(\d+)$/, (_, body) => {
    const current = getState();
    current.user = { ...current.user, ...body, updated_at: now() };
    save();
    return current.user;
  }],

  // ----------------------------------------------------------- jobs
  ["GET", /^\/jobs\/?$/, () => getState().jobs],

  ["GET", /^\/jobs\/(\d+)$/, ([jobId]) => findJob(jobId)],

  // -------------------------------------------------------- matches
  ["GET", /^\/matches\/(\d+)$/, () => getState().matches],

  ["POST", /^\/matches\/(\d+)\/generate$/, () => getState().matches],

  // -------------------------------------------------- notifications
  ["GET", /^\/notifications\/(\d+)$/, () =>
    [...getState().notifications].sort((a, b) =>
      b.created_at.localeCompare(a.created_at),
    )],

  ["PATCH", /^\/notifications\/(\d+)\/read$/, ([notificationId]) => {
    const notification =
      getState().notifications.find((item) => item.id === notificationId) ??
      notFound("Notification");

    notification.read_at = notification.read_at ?? now();
    save();
    return notification;
  }],

  // ------------------------------------------------------ saved jobs
  ["GET", /^\/saved-jobs\/(\d+)$/, () =>
    [...getState().savedJobs].sort((a, b) =>
      b.created_at.localeCompare(a.created_at),
    )],

  ["GET", /^\/saved-jobs\/(\d+)\/(\d+)$/, ([, jobId]) =>
    getState().savedJobs.find((saved) => saved.job_id === jobId) ??
    notFound("Saved job")],

  ["POST", /^\/saved-jobs\/?$/, (_, body) => {
    const current = getState();
    const jobId = Number(body.job_id);

    if (current.savedJobs.some((saved) => saved.job_id === jobId)) {
      throw new Error("Job is already saved");
    }

    const saved: SavedJob = {
      id: nextId(current.savedJobs),
      user_id: DEMO_USER_ID,
      job_id: jobId,
      created_at: now(),
      job: findJob(jobId),
    };

    current.savedJobs.push(saved);
    save();
    return saved;
  }],

  ["DELETE", /^\/saved-jobs\/(\d+)\/(\d+)$/, ([userId, jobId]) => {
    const current = getState();
    current.savedJobs = current.savedJobs.filter(
      (saved) => saved.job_id !== jobId,
    );
    save();
    return { message: "Job removed from saved jobs", user_id: userId, job_id: jobId };
  }],

  // ---------------------------------------------------- applications
  ["GET", /^\/applications\/(\d+)$/, () =>
    [...getState().applications].sort((a, b) =>
      b.applied_at.localeCompare(a.applied_at),
    )],

  ["GET", /^\/applications\/(\d+)\/(\d+)$/, ([, jobId]) =>
    getState().applications.find((item) => item.job_id === jobId) ??
    notFound("Application")],

  ["POST", /^\/applications\/?$/, (_, body) => {
    const current = getState();
    const jobId = Number(body.job_id);

    if (current.applications.some((item) => item.job_id === jobId)) {
      throw new Error("Application already exists for this job");
    }

    const application: Application = {
      id: nextId(current.applications),
      user_id: DEMO_USER_ID,
      job_id: jobId,
      status: "applied",
      applied_at: now(),
      notes: (body.notes as string | null | undefined) ?? null,
      job: findJob(jobId),
    };

    current.applications.push(application);
    save();
    return application;
  }],

  ["PATCH", /^\/applications\/(\d+)\/(\d+)$/, ([, jobId], body) => {
    const application =
      getState().applications.find((item) => item.job_id === jobId) ??
      notFound("Application");

    if (typeof body.status === "string") {
      application.status = body.status;
    }

    if (body.notes !== undefined && body.notes !== null) {
      application.notes = body.notes as string;
    }

    save();
    return application;
  }],

  ["DELETE", /^\/applications\/(\d+)\/(\d+)$/, ([userId, jobId]) => {
    const current = getState();
    current.applications = current.applications.filter(
      (item) => item.job_id !== jobId,
    );
    save();
    return { message: "Application deleted", user_id: userId, job_id: jobId };
  }],
];

export async function handleDemoRequest<T>(
  method: string,
  endpoint: string,
  body?: BodyInit | null,
): Promise<T> {
  // A short pause so loading states behave as they do with the real API.
  await new Promise((resolve) => setTimeout(resolve, 150));

  const path = endpoint.split("?")[0];
  const data =
    typeof body === "string" ? (JSON.parse(body) as Record<string, unknown>) : {};

  for (const [routeMethod, pattern, handler] of routes) {
    const match = method === routeMethod && pattern.exec(path);

    if (match) {
      const params = match.slice(1).map(Number);

      // Copies, so pages can't change the demo state by accident.
      return JSON.parse(JSON.stringify(handler(params, data))) as T;
    }
  }

  throw new Error("This action isn't available in the demo.");
}
