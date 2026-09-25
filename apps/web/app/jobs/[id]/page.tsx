"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Bookmark,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  ExternalLink,
  LoaderCircle,
  MapPin,
  Wallet,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import { getJob } from "@/lib/api/jobs";
import { getUserMatches } from "@/lib/api/matches";
import {
  getSavedJob,
  saveJob,
  unsaveJob,
} from "@/lib/api/saved-jobs";

import type { Job, MatchedJob } from "@/types/api";

import styles from "./page.module.css";

const USER_ID = Number(process.env.NEXT_PUBLIC_DEV_USER_ID || "3");

export default function JobDetailsPage() {
  const params = useParams();
  const jobId = Number(params.id);

  const [job, setJob] = useState<Job | null>(null);
  const [match, setMatch] = useState<MatchedJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isSaved, setIsSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadJob() {
      if (!Number.isFinite(jobId)) {
        setError("Invalid job ID.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const [jobResult, matchesResult] = await Promise.all([
          getJob(jobId),
          getUserMatches(USER_ID),
        ]);

        setJob(jobResult);

        const userMatch =
          matchesResult.find((item) => item.job_id === jobId) ?? null;

        setMatch(userMatch);

        try {
          await getSavedJob(USER_ID, jobId);
          setIsSaved(true);
        } catch {
          setIsSaved(false);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load this job.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadJob();
  }, [jobId]);

  const handleSaveToggle = async () => {
    if (!job || saving) {
      return;
    }

    setSaving(true);

    try {
      if (isSaved) {
        await unsaveJob(USER_ID, job.id);
        setIsSaved(false);
      } else {
        await saveJob({
          user_id: USER_ID,
          job_id: job.id,
        });
        setIsSaved(true);
      }
    } catch (err) {
      console.error("Failed to update saved job:", err);
    } finally {
      setSaving(false);
    }
  };

  const matchReasons = useMemo(() => {
    if (!match?.match_reasons) {
      return [];
    }

    return match.match_reasons
      .split(";")
      .map((reason) => reason.trim())
      .filter(Boolean);
  }, [match]);

  const formattedPostedDate = useMemo(() => {
    if (!job?.posted_at) {
      return null;
    }

    const date = new Date(job.posted_at);

    if (Number.isNaN(date.getTime())) {
      return null;
    }

    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  }, [job]);

  const salary = useMemo(() => {
    if (!job) {
      return null;
    }

    if (job.salary_min === null && job.salary_max === null) {
      return null;
    }

    if (job.salary_min !== null && job.salary_max !== null) {
      return `$${job.salary_min.toLocaleString()} – $${job.salary_max.toLocaleString()}`;
    }

    if (job.salary_min !== null) {
      return `From $${job.salary_min.toLocaleString()}`;
    }

    return `Up to $${job.salary_max?.toLocaleString()}`;
  }, [job]);

  return (
    <AppShell>
      <div className={styles.page}>
        {loading ? (
          <div className={styles.loading}>
            <LoaderCircle
              size={22}
              className={styles.spinner}
            />
            <span>Loading job details...</span>
          </div>
        ) : error || !job ? (
          <div className={styles.errorState}>
            <CircleAlert size={24} />

            <h2>Unable to load this job</h2>

            <p>
              {error || "The requested job could not be found."}
            </p>

            <Link
              href="/jobs"
              className={styles.backButton}
            >
              <ArrowLeft size={16} strokeWidth={1.8} />
              Back to jobs
            </Link>
          </div>
        ) : (
          <>
            <Link
              href="/jobs"
              className={styles.backLink}
            >
              <ArrowLeft size={16} strokeWidth={1.8} />
              Back to jobs
            </Link>

            <section className={styles.jobHero}>
              <div className={styles.heroMain}>
                <div className={styles.companyIcon}>
                  <Building2
                    size={23}
                    strokeWidth={1.8}
                  />
                </div>

                <div className={styles.heroText}>
                  <p className={styles.company}>
                    {job.company}
                  </p>

                  <h1 className={styles.title}>
                    {job.title}
                  </h1>

                  <div className={styles.heroMeta}>
                    {job.location && (
                      <span>
                        <MapPin
                          size={14}
                          strokeWidth={1.8}
                        />
                        {job.location}
                      </span>
                    )}

                    {job.work_type && (
                      <span>
                        <Briefcase
                          size={14}
                          strokeWidth={1.8}
                        />
                        {job.work_type}
                      </span>
                    )}

                    {formattedPostedDate && (
                      <span>
                        <CalendarDays
                          size={14}
                          strokeWidth={1.8}
                        />
                        Posted {formattedPostedDate}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {match && (
                <div className={styles.matchBox}>
                  <span className={styles.matchLabel}>
                    Your match
                  </span>

                  <strong className={styles.matchScore}>
                    {Math.round(match.score)}%
                  </strong>

                  <span className={styles.matchDescription}>
                    Based on your career profile
                  </span>
                </div>
              )}
            </section>

            <div className={styles.contentGrid}>
              <main className={styles.mainContent}>
                <section className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <p className={styles.sectionEyebrow}>
                      Job description
                    </p>

                    <h2 className={styles.sectionTitle}>
                      About this opportunity
                    </h2>
                  </div>

                  {job.description ? (
                    <div className={styles.description}>
                      {job.description
                        .split("\n")
                        .map((paragraph, index) => (
                          <p key={index}>
                            {paragraph}
                          </p>
                        ))}
                    </div>
                  ) : (
                    <p className={styles.noData}>
                      No job description is available for this
                      opportunity.
                    </p>
                  )}
                </section>

                {match && matchReasons.length > 0 && (
                  <section className={styles.section}>
                    <div className={styles.sectionHeader}>
                      <p className={styles.sectionEyebrow}>
                        Match analysis
                      </p>

                      <h2 className={styles.sectionTitle}>
                        Why this job matches you
                      </h2>
                    </div>

                    <div className={styles.reasonList}>
                      {matchReasons.map((reason, index) => (
                        <div
                          key={`${match.id}-${index}`}
                          className={styles.reasonItem}
                        >
                          <CheckCircle2
                            size={17}
                            strokeWidth={1.8}
                          />

                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </main>

              <aside className={styles.sidebar}>
                <section className={styles.detailsCard}>
                  <h2 className={styles.cardTitle}>
                    Job details
                  </h2>

                  <div className={styles.detailList}>
                    {salary && (
                      <div className={styles.detailItem}>
                        <div className={styles.detailIcon}>
                          <Wallet
                            size={16}
                            strokeWidth={1.8}
                          />
                        </div>

                        <div>
                          <span className={styles.detailLabel}>
                            Salary
                          </span>

                          <strong className={styles.detailValue}>
                            {salary}
                          </strong>
                        </div>
                      </div>
                    )}

                    {job.location && (
                      <div className={styles.detailItem}>
                        <div className={styles.detailIcon}>
                          <MapPin
                            size={16}
                            strokeWidth={1.8}
                          />
                        </div>

                        <div>
                          <span className={styles.detailLabel}>
                            Location
                          </span>

                          <strong className={styles.detailValue}>
                            {job.location}
                          </strong>
                        </div>
                      </div>
                    )}

                    {job.work_type && (
                      <div className={styles.detailItem}>
                        <div className={styles.detailIcon}>
                          <Briefcase
                            size={16}
                            strokeWidth={1.8}
                          />
                        </div>

                        <div>
                          <span className={styles.detailLabel}>
                            Work type
                          </span>

                          <strong className={styles.detailValue}>
                            {job.work_type}
                          </strong>
                        </div>
                      </div>
                    )}

                    <div className={styles.detailItem}>
                      <div className={styles.detailIcon}>
                        <Building2
                          size={16}
                          strokeWidth={1.8}
                        />
                      </div>

                      <div>
                        <span className={styles.detailLabel}>
                          Company
                        </span>

                        <strong className={styles.detailValue}>
                          {job.company}
                        </strong>
                      </div>
                    </div>

                    <div className={styles.detailItem}>
                      <div className={styles.detailIcon}>
                        <ExternalLink
                          size={16}
                          strokeWidth={1.8}
                        />
                      </div>

                      <div>
                        <span className={styles.detailLabel}>
                          Source
                        </span>

                        <strong className={styles.detailValue}>
                          {job.source}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className={styles.actionButtons}>
                    <a
                      href={job.application_url}
                      target="_blank"
                      rel="noreferrer"
                      className={styles.applyButton}
                    >
                      Apply for this job
                      <ArrowRight
                        size={16}
                        strokeWidth={1.8}
                      />
                    </a>

                    <button
                      type="button"
                      className={styles.saveButton}
                      onClick={handleSaveToggle}
                      disabled={saving}
                    >
                      <Bookmark
                        size={18}
                        strokeWidth={1.8}
                        fill={
                          isSaved
                            ? "currentColor"
                            : "none"
                        }
                      />

                      {saving
                        ? "Saving..."
                        : isSaved
                          ? "Saved"
                          : "Save Job"}
                    </button>
                  </div>
                </section>
              </aside>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}