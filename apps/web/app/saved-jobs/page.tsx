"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Bookmark,
  Briefcase,
  Building2,
  CalendarDays,
  CircleAlert,
  LoaderCircle,
  MapPin,
  Trash2,
  Wallet,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import {
  getSavedJobs,
  unsaveJob,
} from "@/lib/api/saved-jobs";

import type { SavedJob } from "@/types/api";

import styles from "./page.module.css";

const USER_ID = Number(
  process.env.NEXT_PUBLIC_DEV_USER_ID || "3",
);

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingJobId, setRemovingJobId] = useState<number | null>(
    null,
  );

  useEffect(() => {
    async function loadSavedJobs() {
      try {
        setLoading(true);
        setError(null);

        const result = await getSavedJobs(USER_ID);

        setSavedJobs(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load your saved jobs.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadSavedJobs();
  }, []);

  const handleRemove = async (jobId: number) => {
    if (removingJobId !== null) {
      return;
    }

    try {
      setRemovingJobId(jobId);

      await unsaveJob(USER_ID, jobId);

      setSavedJobs((currentJobs) =>
        currentJobs.filter(
          (savedJob) => savedJob.job_id !== jobId,
        ),
      );
    } catch (err) {
      console.error("Failed to remove saved job:", err);
    } finally {
      setRemovingJobId(null);
    }
  };

  const formatSavedDate = (dateString: string) => {
    const date = new Date(dateString);

    if (Number.isNaN(date.getTime())) {
      return null;
    }

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatSalary = (
    salaryMin: number | null,
    salaryMax: number | null,
  ) => {
    if (salaryMin === null && salaryMax === null) {
      return null;
    }

    if (salaryMin !== null && salaryMax !== null) {
      return `$${salaryMin.toLocaleString()} – $${salaryMax.toLocaleString()}`;
    }

    if (salaryMin !== null) {
      return `From $${salaryMin.toLocaleString()}`;
    }

    return `Up to $${salaryMax?.toLocaleString()}`;
  };

  return (
    <AppShell>
      <div className={styles.page}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Your collection</p>

            <h1 className={styles.title}>Saved Jobs</h1>

            <p className={styles.subtitle}>
              Keep track of opportunities you want to revisit
              and apply to later.
            </p>
          </div>

          {!loading && !error && (
            <div className={styles.countBadge}>
              <Bookmark size={15} strokeWidth={1.8} />
              <span>
                {savedJobs.length}{" "}
                {savedJobs.length === 1 ? "saved job" : "saved jobs"}
              </span>
            </div>
          )}
        </header>

        {loading ? (
          <div className={styles.loading}>
            <LoaderCircle
              size={21}
              className={styles.spinner}
            />
            <span>Loading your saved jobs...</span>
          </div>
        ) : error ? (
          <div className={styles.errorState}>
            <div className={styles.stateIcon}>
              <CircleAlert size={22} />
            </div>

            <h2>Unable to load saved jobs</h2>

            <p>{error}</p>
          </div>
        ) : savedJobs.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <Bookmark size={25} strokeWidth={1.7} />
            </div>

            <h2>No saved jobs yet</h2>

            <p>
              When you find a job you want to come back to,
              save it and it will appear here.
            </p>

            <Link
              href="/jobs"
              className={styles.browseButton}
            >
              Browse jobs
              <ArrowRight size={16} strokeWidth={1.8} />
            </Link>
          </div>
        ) : (
          <section className={styles.jobsSection}>
            <div className={styles.sectionHeader}>
              <div>
                <p className={styles.sectionEyebrow}>
                  Your opportunities
                </p>

                <h2 className={styles.sectionTitle}>
                  Jobs you've saved
                </h2>
              </div>

              <span className={styles.resultCount}>
                {savedJobs.length}{" "}
                {savedJobs.length === 1
                  ? "opportunity"
                  : "opportunities"}
              </span>
            </div>

            <div className={styles.jobList}>
              {savedJobs.map((savedJob) => {
                const job = savedJob.job;

                const salary = formatSalary(
                  job.salary_min,
                  job.salary_max,
                );

                const savedDate = formatSavedDate(
                  savedJob.created_at,
                );

                const isRemoving =
                  removingJobId === job.id;

                return (
                  <article
                    key={savedJob.id}
                    className={styles.jobCard}
                  >
                    <div className={styles.jobIcon}>
                      <Building2
                        size={21}
                        strokeWidth={1.8}
                      />
                    </div>

                    <div className={styles.jobContent}>
                      <div className={styles.jobHeader}>
                        <div className={styles.jobIdentity}>
                          <p className={styles.company}>
                            {job.company}
                          </p>

                          <Link
                            href={`/jobs/${job.id}`}
                            className={styles.jobTitleLink}
                          >
                            <h3 className={styles.jobTitle}>
                              {job.title}
                            </h3>
                          </Link>
                        </div>

                        <div className={styles.savedLabel}>
                          <Bookmark
                            size={14}
                            strokeWidth={1.8}
                            fill="currentColor"
                          />
                          Saved
                        </div>
                      </div>

                      <div className={styles.meta}>
                        {job.location && (
                          <span>
                            <MapPin
                              size={13}
                              strokeWidth={1.8}
                            />
                            {job.location}
                          </span>
                        )}

                        {job.work_type && (
                          <span>
                            <Briefcase
                              size={13}
                              strokeWidth={1.8}
                            />
                            {job.work_type}
                          </span>
                        )}

                        {salary && (
                          <span>
                            <Wallet
                              size={13}
                              strokeWidth={1.8}
                            />
                            {salary}
                          </span>
                        )}

                        {savedDate && (
                          <span>
                            <CalendarDays
                              size={13}
                              strokeWidth={1.8}
                            />
                            Saved {savedDate}
                          </span>
                        )}
                      </div>

                      <div className={styles.actions}>
                        <Link
                          href={`/jobs/${job.id}`}
                          className={styles.viewButton}
                        >
                          View job
                          <ArrowRight
                            size={15}
                            strokeWidth={1.8}
                          />
                        </Link>

                        <button
                          type="button"
                          className={styles.removeButton}
                          onClick={() =>
                            handleRemove(job.id)
                          }
                          disabled={isRemoving}
                        >
                          <Trash2
                            size={15}
                            strokeWidth={1.8}
                          />

                          {isRemoving
                            ? "Removing..."
                            : "Remove"}
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}