import Link from "next/link";
import { ArrowRight, Bell, CheckCircle2 } from "lucide-react";

import type { Notification } from "@/types/api";

import styles from "./RecentNotifications.module.css";

interface RecentNotificationsProps {
  notifications: Notification[];
}

export default function RecentNotifications({
  notifications,
}: RecentNotificationsProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Activity</p>

          <h2 className={styles.title}>
            Recent notifications
          </h2>
        </div>

        <Link href="/notifications" className={styles.viewAll}>
          View all
          <ArrowRight size={15} strokeWidth={1.8} />
        </Link>
      </div>

      <div className={styles.list}>
        {notifications.length === 0 ? (
          <div className={styles.empty}>
            <Bell size={20} strokeWidth={1.7} />

            <p>No notifications yet.</p>
          </div>
        ) : (
          notifications.slice(0, 5).map((notification) => (
            <div
              key={notification.id}
              className={`${styles.item} ${
                !notification.read_at
                  ? styles.unread
                  : ""
              }`}
            >
              <div className={styles.icon}>
                {notification.read_at ? (
                  <CheckCircle2
                    size={18}
                    strokeWidth={1.7}
                  />
                ) : (
                  <Bell size={18} strokeWidth={1.7} />
                )}
              </div>

              <div className={styles.content}>
                <p className={styles.notificationTitle}>
                  {notification.title}
                </p>

                {notification.message && (
                  <p className={styles.message}>
                    {notification.message}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}