"use client";

import {
  DEV_USER_ID as USER_ID,
  HIGH_MATCH_SCORE,
} from "@/lib/config";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, LoaderCircle } from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import DashboardStats from "@/components/dashboard/DashboardStats";
import MatchCard from "@/components/dashboard/MatchCard";
import RecentNotifications from "@/components/dashboard/RecentNotifications";
import ApplicationPipeline from "@/components/dashboard/ApplicationPipeline";

import { getCareerProfile } from "@/lib/api/career-profile";
import { getUserMatches } from "@/lib/api/matches";
import { getNotifications } from "@/lib/api/notifications";
import {
  getApplications,
  getSavedJobs,
  saveJob,
  unsaveJob,
} from "@/lib/api/saved-jobs";

import type {
  Application,
  CareerProfile,
  MatchedJob,
  Notification,
} from "@/types/api";

import styles from "./page.module.css";


export default function HomePage() {
  const [matches, setMatches] = useState<MatchedJob[]>([]);
  const [notifications, setNotifications] = useState<
    Notification[]
  >([]);
  const [applications, setApplications] = useState<
    Application[]
  >([]);
  const [profile, setProfile] =
    useState<CareerProfile | null>(null);

  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(
    new Set(),
  );
  const [savingJobId, setSavingJobId] = useState<number | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [
          matchesResult,
          notificationsResult,
          applicationsResult,
          savedJobsResult,
        ] = await Promise.all([
          getUserMatches(USER_ID),
          getNotifications(USER_ID),
          getApplications(USER_ID),
          getSavedJobs(USER_ID),
        ]);

        setMatches(matchesResult);
        setSavedJobIds(
          new Set(savedJobsResult.map((saved) => saved.job_id)),
        );
        setNotifications(notificationsResult);
        setApplications(applicationsResult);

        try {
          const profileResult =
            await getCareerProfile(USER_ID);

          setProfile(profileResult);
        } catch {
          setProfile(null);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dashboard data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const toggleSave = async (match: MatchedJob) => {
    if (savingJobId !== null) {
      return;
    }

    const wasSaved = savedJobIds.has(match.job_id);

    setSavingJobId(match.job_id);

    try {
      if (wasSaved) {
        await unsaveJob(USER_ID, match.job_id);
      } else {
        await saveJob({ user_id: USER_ID, job_id: match.job_id });
      }

      setSavedJobIds((current) => {
        const next = new Set(current);

        if (wasSaved) {
          next.delete(match.job_id);
        } else {
          next.add(match.job_id);
        }

        return next;
      });
    } catch (err) {
      console.error("Failed to update saved job:", err);
    } finally {
      setSavingJobId(null);
    }
  };

  const highMatches = matches.filter(
    (match) => match.score >= HIGH_MATCH_SCORE,
  ).length;

  const unreadNotifications = notifications.filter(
    (notification) => !notification.read_at,
  ).length;

  const interviews = applications.filter(
    (application) => application.status === "interview",
  ).length;

  const offers = applications.filter(
    (application) => application.status === "offer",
  ).length;

  const topMatches = matches
    .filter((match) => match.score >= HIGH_MATCH_SCORE)
    .slice(0, 5);

  return (
    <AppShell>
      <div className={styles.page}>
        <section className={styles.hero}>
          <div>
            <p className={styles.eyebrow}>Dashboard</p>

            <h2 className={styles.heading}>
              Your job search at a glance.
            </h2>

            <p className={styles.subtitle}>
              Track your matches and stay on top of new
              opportunities.
            </p>
          </div>

          <Link
            href="/jobs"
            className={styles.jobsButton}
          >
            Explore jobs
            <ArrowRight
              size={16}
              strokeWidth={1.8}
            />
          </Link>
        </section>

        {loading ? (
          <div className={styles.loading}>
            <LoaderCircle
              size={20}
              className={styles.spinner}
            />

            <span>
              Loading your dashboard...
            </span>
          </div>
        ) : error ? (
          <div className={styles.error}>
            <strong>
              Unable to load your dashboard.
            </strong>

            <p>{error}</p>
          </div>
        ) : (
          <>
            <DashboardStats
              totalMatches={matches.length}
              highMatches={highMatches}
              applications={applications.length}
              unreadNotifications={unreadNotifications}
              interviews={interviews}
              offers={offers}
            />

            <ApplicationPipeline
              applications={applications}
            />

            <div className={styles.contentGrid}>
              <section
                className={styles.matchesSection}
              >
                <div
                  className={styles.sectionHeader}
                >
                  <div>
                    <p
                      className={
                        styles.sectionEyebrow
                      }
                    >
                      Recommendations
                    </p>

                    <h2
                      className={
                        styles.sectionTitle
                      }
                    >
                      High-quality matches
                    </h2>
                  </div>

                  <Link
                    href="/jobs"
                    className={styles.viewAll}
                  >
                    View all

                    <ArrowRight
                      size={15}
                      strokeWidth={1.8}
                    />
                  </Link>
                </div>

                {topMatches.length === 0 ? (
                  <div className={styles.empty}>
                    <h3>
                      No high-quality matches yet
                    </h3>

                    <p>
                      Once jobs reach a {HIGH_MATCH_SCORE}% or higher
                      match score, they will appear
                      here.
                    </p>

                    {!profile && (
                      <Link href="/profile">
                        Complete your career profile
                      </Link>
                    )}
                  </div>
                ) : (
                  <div
                    className={styles.matchList}
                  >
                    {topMatches.map((match) => (
                      <MatchCard
                        key={match.id}
                        match={match}
                        isSaved={savedJobIds.has(
                          match.job_id,
                        )}
                        saving={savingJobId === match.job_id}
                        onToggleSave={toggleSave}
                      />
                    ))}
                  </div>
                )}
              </section>

              <RecentNotifications
                notifications={notifications}
                onNotificationRead={(updatedNotification) => {
                  setNotifications((currentNotifications) =>
                    currentNotifications.map((notification) =>
                      notification.id === updatedNotification.id
                        ? updatedNotification
                        : notification,
                    ),
                  );
                }}
              />
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}