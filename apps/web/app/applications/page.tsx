"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BriefcaseBusiness,
  Briefcase,
  Building2,
  CalendarDays,
  CircleAlert,
  LoaderCircle,
  MapPin,
  Trash2,
  Wallet,
  RefreshCw,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import { getApplications } from "@/lib/api/saved-jobs";

import type { Application } from "@/types/api";

import styles from "./page.module.css";

const USER_ID = Number(
  process.env.NEXT_PUBLIC_DEV_USER_ID || "5",
);

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>(
    [],
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadApplications() {
      try {
        setLoading(true);
        setError(null);

        const result = await getApplications(USER_ID);

        setApplications(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load your applications.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadApplications();
  }, []);

  const formatAppliedDate = (dateString: string) => {
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

  const getStatusLabel = (status: string) => {
    return status.replace(/_/g, " ");
  };

  return (
    <AppShell>
      <div className={styles.page}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Your applications</p>

            <h1 className={styles.title}>Applications</h1>

            <p className={styles.subtitle}>
              Track the jobs you've applied to and follow each
              opportunity through your application process.
            </p>
          </div>

          {!loading && !error && (
            <div className={styles.countBadge}>
              <BriefcaseBusiness
                size={15}
                strokeWidth={1.8}
              />

              <span>
                {applications.length}{" "}
                {applications.length === 1
                  ? "application"
                  : "applications"}
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

            <span>Loading your applications...</span>
          </div>
        ) : error ? (
          <div className={styles.errorState}>
            <div className={styles.stateIcon}>
              <CircleAlert size={22} />
            </div>

            <h2>Unable to load applications</h2>

            <p>{error}</p>
          </div>
        ) : applications.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <BriefcaseBusiness
                size={25}
                strokeWidth={1.7}
              />
            </div>

            <h2>No applications yet</h2>

            <p>
              When you apply to a job, add it to JobForge so you
              can keep track of its progress here.
            </p>

            <Link
              href="/jobs"
              className={styles.browseButton}
            >
              Browse jobs
              <ArrowRight
                size={16}
                strokeWidth={1.8}
              />
            </Link>
          </div>
        ) : (
          <section className={styles.applicationsSection}>
            <div className={styles.sectionHeader}>
              <div>
                <p className={styles.sectionEyebrow}>
                  Your pipeline
                </p>

                <h2 className={styles.sectionTitle}>
                  Jobs you've applied to
                </h2>
              </div>

              <span className={styles.resultCount}>
                {applications.length}{" "}
                {applications.length === 1
                  ? "opportunity"
                  : "opportunities"}
              </span>
            </div>

            <div className={styles.applicationList}>
              {applications.map((application) => {
                const job = application.job;

                const salary = formatSalary(
                  job.salary_min,
                  job.salary_max,
                );

                const appliedDate = formatAppliedDate(
                  application.applied_at,
                );

                return (
                  <article
                    key={application.id}
                    className={styles.applicationCard}
                  >
                    <div className={styles.applicationIcon}>
                      <Building2
                        size={21}
                        strokeWidth={1.8}
                      />
                    </div>

                    <div className={styles.applicationContent}>
                      <div className={styles.applicationHeader}>
                        <div className={styles.applicationIdentity}>
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

                        <div className={styles.statusBadge}>
                          <span className={styles.statusDot} />

                          {getStatusLabel(
                            application.status,
                          )}
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

                        {appliedDate && (
                          <span>
                            <CalendarDays
                              size={13}
                              strokeWidth={1.8}
                            />

                            Applied {appliedDate}
                          </span>
                        )}
                      </div>

                      {application.notes && (
                        <div className={styles.notes}>
                          <span className={styles.notesLabel}>
                            Notes
                          </span>

                          {application.notes}
                        </div>
                      )}

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
                          className={styles.updateButton}
                        >
                          <RefreshCw
                            size={15}
                            strokeWidth={1.8}
                          />

                          Update status
                        </button>

                        <button
                          type="button"
                          className={styles.deleteButton}
                        >
                          <Trash2
                            size={15}
                            strokeWidth={1.8}
                          />

                          Delete
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