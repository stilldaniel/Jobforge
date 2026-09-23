"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, LoaderCircle } from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import DashboardStats from "@/components/dashboard/DashboardStats";
import MatchCard from "@/components/dashboard/MatchCard";
import RecentNotifications from "@/components/dashboard/RecentNotifications";

import { getCareerProfile } from "@/lib/api/career-profile";
import { getUserMatches } from "@/lib/api/matches";
import { getUserNotifications } from "@/lib/api/notiications";

import type {
  CareerProfile,
  MatchedJob,
  Notification,
} from "@/types/api";

import styles from "./page.module.css";

const USER_ID = Number(
  process.env.NEXT_PUBLIC_DEV_USER_ID || "3",
);

export default function HomePage() {
  const [matches, setMatches] = useState<MatchedJob[]>([]);
  const [notifications, setNotifications] = useState<
    Notification[]
  >([]);
  const [profile, setProfile] =
    useState<CareerProfile | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [matchesResult, notificationsResult] =
          await Promise.all([
            getUserMatches(USER_ID),
            getUserNotifications(USER_ID),
          ]);

        setMatches(matchesResult);
        setNotifications(notificationsResult);

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

  const highMatches = matches.filter(
    (match) => match.score >= 91,
  ).length;

  const unreadNotifications = notifications.filter(
    (notification) => !notification.read_at,
  ).length;

  const topMatches = matches.slice(0, 5);

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

          <Link href="/jobs" className={styles.jobsButton}>
            Explore jobs
            <ArrowRight size={16} strokeWidth={1.8} />
          </Link>
        </section>

        {loading ? (
          <div className={styles.loading}>
            <LoaderCircle
              size={20}
              className={styles.spinner}
            />
            <span>Loading your dashboard...</span>
          </div>
        ) : error ? (
          <div className={styles.error}>
            <strong>Unable to load your dashboard.</strong>

            <p>{error}</p>
          </div>
        ) : (
          <>
            <DashboardStats
              totalMatches={matches.length}
              highMatches={highMatches}
              unreadNotifications={unreadNotifications}
              profileComplete={profile !== null}
            />

            <div className={styles.contentGrid}>
              <section className={styles.matchesSection}>
                <div className={styles.sectionHeader}>
                  <div>
                    <p className={styles.sectionEyebrow}>
                      Recommendations
                    </p>

                    <h2 className={styles.sectionTitle}>
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
                    <h3>No matches yet</h3>

                    <p>
                      Once jobs are matched against your
                      career profile, they will appear here.
                    </p>

                    {!profile && (
                      <Link href="/profile">
                        Complete your career profile
                      </Link>
                    )}
                  </div>
                ) : (
                  <div className={styles.matchList}>
                    {topMatches.map((match) => (
                      <MatchCard
                        key={match.id}
                        match={match}
                      />
                    ))}
                  </div>
                )}
              </section>

              <RecentNotifications
                notifications={notifications}
              />
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}