"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Bell,
  Check,
  CheckCircle2,
  LoaderCircle,
} from "lucide-react";

import type { Notification } from "@/types/api";

import { markNotificationAsRead } from "@/lib/api/notifications";

import styles from "./RecentNotifications.module.css";

interface RecentNotificationsProps {
  notifications: Notification[];
  onNotificationRead: (
    notification: Notification,
  ) => void;
}

export default function RecentNotifications({
  notifications,
  onNotificationRead,
}: RecentNotificationsProps) {
  const [readingNotificationId, setReadingNotificationId] =
    useState<number | null>(null);

  const handleMarkAsRead = async (
    notification: Notification,
  ) => {
    if (
      notification.read_at ||
      readingNotificationId !== null
    ) {
      return;
    }

    try {
      setReadingNotificationId(notification.id);

      const updatedNotification =
        await markNotificationAsRead(
          notification.id,
        );

      onNotificationRead(updatedNotification);
    } catch (error) {
      console.error(
        "Failed to mark notification as read:",
        error,
      );
    } finally {
      setReadingNotificationId(null);
    }
  };

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Activity</p>

          <h2 className={styles.title}>
            Recent notifications
          </h2>
        </div>

        <Link
          href="/notifications"
          className={styles.viewAll}
        >
          View all
          <ArrowRight
            size={15}
            strokeWidth={1.8}
          />
        </Link>
      </div>

      <div className={styles.list}>
        {notifications.length === 0 ? (
          <div className={styles.empty}>
            <Bell
              size={20}
              strokeWidth={1.7}
            />

            <p>No notifications yet.</p>
          </div>
        ) : (
          notifications
            .slice(0, 5)
            .map((notification) => {
              const isUnread =
                !notification.read_at;

              const isReading =
                readingNotificationId ===
                notification.id;

              return (
                <div
                  key={notification.id}
                  className={`${styles.item} ${
                    isUnread
                      ? styles.unread
                      : ""
                  }`}
                >
                  <div className={styles.icon}>
                    {isUnread ? (
                      <Bell
                        size={18}
                        strokeWidth={1.7}
                      />
                    ) : (
                      <CheckCircle2
                        size={18}
                        strokeWidth={1.7}
                      />
                    )}
                  </div>

                  <div className={styles.content}>
                    <div
                      className={
                        styles.titleRow
                      }
                    >
                      <p
                        className={
                          styles.notificationTitle
                        }
                      >
                        {notification.title}
                      </p>

                      {isUnread && (
                        <span
                          className={
                            styles.unreadDot
                          }
                          aria-label="Unread"
                        />
                      )}
                    </div>

                    {notification.message && (
                      <p className={styles.message}>
                        {notification.message}
                      </p>
                    )}

                    {isUnread && (
                      <button
                        type="button"
                        className={
                          styles.markReadButton
                        }
                        onClick={() =>
                          handleMarkAsRead(
                            notification,
                          )
                        }
                        disabled={isReading}
                      >
                        {isReading ? (
                          <>
                            <LoaderCircle
                              size={12}
                              className={
                                styles.spinner
                              }
                            />
                            Marking as read...
                          </>
                        ) : (
                          <>
                            <Check
                              size={12}
                              strokeWidth={2}
                            />
                            Mark as read
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })
        )}
      </div>
    </section>
  );
}