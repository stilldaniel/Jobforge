"use client";

import { DEV_USER_ID as USER_ID } from "@/lib/config";
import { formatSalary } from "@/lib/format";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BriefcaseBusiness,
  Briefcase,
  Building2,
  CalendarDays,
  Check,
  CircleAlert,
  LoaderCircle,
  MapPin,
  Trash2,
  Wallet,
  RefreshCw,
  X,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import {
  getApplications,
  updateApplication,
  deleteApplication,
} from "@/lib/api/saved-jobs";

import type { Application } from "@/types/api";

import styles from "./page.module.css";


const APPLICATION_STATUSES = [
  "applied",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
] as const;

type ApplicationStatus =
  (typeof APPLICATION_STATUSES)[number];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<
    Application[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingApplicationId, setEditingApplicationId] =
    useState<number | null>(null);

  const [selectedStatus, setSelectedStatus] =
    useState<ApplicationStatus>("applied");

  const [updatingApplicationId, setUpdatingApplicationId] =
    useState<number | null>(null);

  const [deletingApplicationId, setDeletingApplicationId] =
    useState<number | null>(null);

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

  const getStatusLabel = (status: string) => {
    return status.replace(/_/g, " ");
  };

  const startStatusEdit = (
    application: Application,
  ) => {
    setEditingApplicationId(application.id);
    setSelectedStatus(
      APPLICATION_STATUSES.includes(
        application.status as ApplicationStatus,
      )
        ? (application.status as ApplicationStatus)
        : "applied",
    );
  };

  const cancelStatusEdit = () => {
    setEditingApplicationId(null);
    setSelectedStatus("applied");
  };

  const handleUpdateStatus = async (
    application: Application,
  ) => {
    if (updatingApplicationId !== null) {
      return;
    }

    try {
      setUpdatingApplicationId(application.id);

      const updatedApplication =
        await updateApplication(
          USER_ID,
          application.job_id,
          {
            status: selectedStatus,
          },
        );

      setApplications((currentApplications) =>
        currentApplications.map((currentApplication) =>
          currentApplication.id === updatedApplication.id
            ? updatedApplication
            : currentApplication,
        ),
      );

      setEditingApplicationId(null);
    } catch (err) {
      console.error(
        "Failed to update application status:",
        err,
      );
    } finally {
      setUpdatingApplicationId(null);
    }
  };

  const handleDeleteApplication = async (
    application: Application,
  ) => {
    if (deletingApplicationId !== null) {
      return;
    }

    const confirmed = window.confirm(
      `Remove your application for ${application.job.title}?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingApplicationId(application.id);

      await deleteApplication(
        USER_ID,
        application.job_id,
      );

      setApplications((currentApplications) =>
        currentApplications.filter(
          (currentApplication) =>
            currentApplication.id !== application.id,
        ),
      );

      if (
        editingApplicationId === application.id
      ) {
        setEditingApplicationId(null);
      }
    } catch (err) {
      console.error(
        "Failed to delete application:",
        err,
      );
    } finally {
      setDeletingApplicationId(null);
    }
  };

  return (
    <AppShell>
      <div className={styles.page}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>
              Your applications
            </p>

            <h1 className={styles.title}>
              Applications
            </h1>

            <p className={styles.subtitle}>
              Track the jobs you've applied to and follow
              each opportunity through your application
              process.
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

            <span>
              Loading your applications...
            </span>
          </div>
        ) : error ? (
          <div className={styles.errorState}>
            <div className={styles.stateIcon}>
              <CircleAlert size={22} />
            </div>

            <h2>
              Unable to load applications
            </h2>

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
              When you apply to a job, add it to JobForge
              so you can keep track of its progress here.
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

                const salary = formatSalary(job);

                const appliedDate =
                  formatAppliedDate(
                    application.applied_at,
                  );

                const isEditing =
                  editingApplicationId ===
                  application.id;

                const isUpdating =
                  updatingApplicationId ===
                  application.id;

                const isDeleting =
                  deletingApplicationId ===
                  application.id;

                return (
                  <article
                    key={application.id}
                    className={styles.applicationCard}
                  >
                    <div
                      className={
                        styles.applicationIcon
                      }
                    >
                      <Building2
                        size={21}
                        strokeWidth={1.8}
                      />
                    </div>

                    <div
                      className={
                        styles.applicationContent
                      }
                    >
                      <div
                        className={
                          styles.applicationHeader
                        }
                      >
                        <div
                          className={
                            styles.applicationIdentity
                          }
                        >
                          <p className={styles.company}>
                            {job.company}
                          </p>

                          <Link
                            href={`/jobs/${job.id}`}
                            className={
                              styles.jobTitleLink
                            }
                          >
                            <h3
                              className={
                                styles.jobTitle
                              }
                            >
                              {job.title}
                            </h3>
                          </Link>
                        </div>

                        <div
                          className={
                            styles.statusBadge
                          }
                        >
                          <span
                            className={
                              styles.statusDot
                            }
                          />

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
                          <span
                            className={
                              styles.notesLabel
                            }
                          >
                            Notes
                          </span>

                          {application.notes}
                        </div>
                      )}

                      {isEditing && (
                        <div
                          className={
                            styles.statusEditor
                          }
                        >
                          <select
                            value={selectedStatus}
                            onChange={(event) =>
                              setSelectedStatus(
                                event.target
                                  .value as ApplicationStatus,
                              )
                            }
                            className={
                              styles.statusSelect
                            }
                            disabled={isUpdating}
                          >
                            {APPLICATION_STATUSES.map(
                              (status) => (
                                <option
                                  key={status}
                                  value={status}
                                >
                                  {getStatusLabel(
                                    status,
                                  )}
                                </option>
                              ),
                            )}
                          </select>

                          <button
                            type="button"
                            className={
                              styles.confirmButton
                            }
                            onClick={() =>
                              handleUpdateStatus(
                                application,
                              )
                            }
                            disabled={isUpdating}
                          >
                            {isUpdating ? (
                              <>
                                <LoaderCircle
                                  size={14}
                                  className={
                                    styles.spinner
                                  }
                                />
                                Saving...
                              </>
                            ) : (
                              <>
                                <Check
                                  size={14}
                                  strokeWidth={1.8}
                                />
                                Save status
                              </>
                            )}
                          </button>

                          <button
                            type="button"
                            className={
                              styles.cancelButton
                            }
                            onClick={
                              cancelStatusEdit
                            }
                            disabled={isUpdating}
                          >
                            <X
                              size={14}
                              strokeWidth={1.8}
                            />
                            Cancel
                          </button>
                        </div>
                      )}

                      <div className={styles.actions}>
                        <Link
                          href={`/jobs/${job.id}`}
                          className={
                            styles.viewButton
                          }
                        >
                          View job

                          <ArrowRight
                            size={15}
                            strokeWidth={1.8}
                          />
                        </Link>

                        {!isEditing && (
                          <button
                            type="button"
                            className={
                              styles.updateButton
                            }
                            onClick={() =>
                              startStatusEdit(
                                application,
                              )
                            }
                            disabled={
                              isDeleting ||
                              updatingApplicationId !==
                                null
                            }
                          >
                            <RefreshCw
                              size={15}
                              strokeWidth={1.8}
                            />

                            Update status
                          </button>
                        )}

                        <button
                          type="button"
                          className={
                            styles.deleteButton
                          }
                          onClick={() =>
                            handleDeleteApplication(
                              application,
                            )
                          }
                          disabled={
                            isDeleting ||
                            isUpdating
                          }
                        >
                          {isDeleting ? (
                            <LoaderCircle
                              size={15}
                              className={
                                styles.spinner
                              }
                            />
                          ) : (
                            <Trash2
                              size={15}
                              strokeWidth={1.8}
                            />
                          )}

                          {isDeleting
                            ? "Deleting..."
                            : "Delete"}
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