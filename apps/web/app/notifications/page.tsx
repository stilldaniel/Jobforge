"use client";

import { DEV_USER_ID as USER_ID } from "@/lib/config";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Bell,
  Briefcase,
  Check,
  CircleAlert,
  LoaderCircle,
  Mail,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import {
  getNotifications,
  markNotificationAsRead,
} from "@/lib/api/notifications";
import { getUserMatches } from "@/lib/api/matches";

import type {
  MatchedJob,
  Notification,
} from "@/types/api";

import styles from "./page.module.css";


export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<
    Notification[]
  >([]);
  const [matches, setMatches] = useState<MatchedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readingNotificationId, setReadingNotificationId] =
    useState<number | null>(null);

  useEffect(() => {
    async function loadNotifications() {
      try {
        setLoading(true);
        setError(null);

        const [notificationsResult, matchesResult] =
          await Promise.all([
            getNotifications(USER_ID),
            getUserMatches(USER_ID),
          ]);

        setNotifications(notificationsResult);
        setMatches(matchesResult);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load your notifications.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadNotifications();
  }, []);

  const matchById = useMemo(() => {
    return new Map(
      matches.map((match) => [match.id, match]),
    );
  }, [matches]);

  const unreadCount = notifications.filter(
    (notification) => notification.read_at === null,
  ).length;

  const formatNotificationDate = (dateString: string) => {
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

  const handleMarkAsRead = async (
    notificationId: number,
  ) => {
    if (readingNotificationId !== null) {
      return;
    }

    try {
      setReadingNotificationId(notificationId);

      const updatedNotification =
        await markNotificationAsRead(notificationId);

      setNotifications((currentNotifications) =>
        currentNotifications.map((notification) =>
          notification.id === updatedNotification.id
            ? updatedNotification
            : notification,
        ),
      );
    } catch (err) {
      console.error(
        "Failed to mark notification as read:",
        err,
      );
    } finally {
      setReadingNotificationId(null);
    }
  };

  return (
    <AppShell>
      <div className={styles.page}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>
              Stay up to date
            </p>

            <h1 className={styles.title}>
              Notifications
            </h1>

            <p className={styles.subtitle}>
              See new job matches and important updates
              from JobForge.
            </p>
          </div>

          {!loading && !error && (
            <div className={styles.countBadge}>
              <Bell size={15} strokeWidth={1.8} />

              <span>
                {unreadCount}{" "}
                {unreadCount === 1
                  ? "unread notification"
                  : "unread notifications"}
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
              Loading your notifications...
            </span>
          </div>
        ) : error ? (
          <div className={styles.errorState}>
            <div className={styles.stateIcon}>
              <CircleAlert size={22} />
            </div>

            <h2>
              Unable to load notifications
            </h2>

            <p>{error}</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <Bell
                size={25}
                strokeWidth={1.7}
              />
            </div>

            <h2>No notifications yet</h2>

            <p>
              When JobForge finds new opportunities that
              match your career profile, they will appear
              here.
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
          <section className={styles.notificationsSection}>
            <div className={styles.sectionHeader}>
              <div>
                <p className={styles.sectionEyebrow}>
                  Your updates
                </p>

                <h2 className={styles.sectionTitle}>
                  Recent notifications
                </h2>
              </div>

              <span className={styles.resultCount}>
                {notifications.length}{" "}
                {notifications.length === 1
                  ? "notification"
                  : "notifications"}
              </span>
            </div>

            <div className={styles.notificationList}>
              {notifications.map((notification) => {
                const match = matchById.get(
                  notification.job_match_id,
                );

                const notificationDate =
                  formatNotificationDate(
                    notification.created_at,
                  );

                const isUnread =
                  notification.read_at === null;

                const isReading =
                  readingNotificationId ===
                  notification.id;

                return (
                  <article
                    key={notification.id}
                    className={`${styles.notificationCard} ${
                      isUnread
                        ? styles.unreadCard
                        : ""
                    }`}
                  >
                    <div
                      className={`${styles.notificationIcon} ${
                        isUnread
                          ? styles.unreadIcon
                          : ""
                      }`}
                    >
                      {notification.channel ===
                      "email" ? (
                        <Mail
                          size={20}
                          strokeWidth={1.8}
                        />
                      ) : (
                        <Bell
                          size={20}
                          strokeWidth={1.8}
                        />
                      )}
                    </div>

                    <div
                      className={
                        styles.notificationContent
                      }
                    >
                      <div
                        className={
                          styles.notificationHeader
                        }
                      >
                        <div>
                          <div
                            className={
                              styles.notificationTitleRow
                            }
                          >
                            {isUnread && (
                              <span
                                className={
                                  styles.unreadDot
                                }
                              />
                            )}

                            <h3
                              className={
                                styles.notificationTitle
                              }
                            >
                              {notification.title}
                            </h3>
                          </div>

                          {notificationDate && (
                            <p
                              className={
                                styles.notificationDate
                              }
                            >
                              {notificationDate}
                            </p>
                          )}
                        </div>

                        {isUnread && (
                          <span
                            className={
                              styles.unreadLabel
                            }
                          >
                            New
                          </span>
                        )}
                      </div>

                      {notification.message && (
                        <p
                          className={
                            styles.notificationMessage
                          }
                        >
                          {notification.message}
                        </p>
                      )}

                      {match && (
                        <div className={styles.jobPreview}>
                          <div
                            className={
                              styles.jobPreviewIcon
                            }
                          >
                            <Briefcase
                              size={15}
                              strokeWidth={1.8}
                            />
                          </div>

                          <div
                            className={
                              styles.jobPreviewContent
                            }
                          >
                            <span
                              className={
                                styles.jobCompany
                              }
                            >
                              {match.company}
                            </span>

                            <span
                              className={
                                styles.jobTitle
                              }
                            >
                              {match.title}
                            </span>
                          </div>
                        </div>
                      )}

                      <div
                        className={styles.actions}
                      >
                        {match && (
                          <Link
                            href={`/jobs/${match.job_id}`}
                            className={styles.viewButton}
                            onClick={() => {
                              if (isUnread) {
                                void handleMarkAsRead(
                                  notification.id,
                                );
                              }
                            }}
                          >
                            View job
                            <ArrowRight
                              size={15}
                              strokeWidth={1.8}
                            />
                          </Link>
                        )}

                        {isUnread && (
                          <button
                            type="button"
                            className={
                              styles.readButton
                            }
                            onClick={() =>
                              handleMarkAsRead(
                                notification.id,
                              )
                            }
                            disabled={isReading}
                          >
                            <Check
                              size={15}
                              strokeWidth={1.8}
                            />

                            {isReading
                              ? "Marking..."
                              : "Mark as read"}
                          </button>
                        )}

                        {!isUnread && (
                          <span
                            className={
                              styles.readLabel
                            }
                          >
                            <Check
                              size={14}
                              strokeWidth={1.8}
                            />
                            Read
                          </span>
                        )}
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