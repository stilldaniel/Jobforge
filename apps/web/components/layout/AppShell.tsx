"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  Briefcase,
  Bookmark,
  ClipboardCheck,
  LayoutDashboard,
  Settings,
  User,
} from "lucide-react";

import styles from "./AppShell.module.css";
import { getNotifications } from "@/lib/api/notifications";

const USER_ID = Number(
  process.env.NEXT_PUBLIC_DEV_USER_ID || "3",
);

const navigation = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Jobs",
    href: "/jobs",
    icon: Briefcase,
  },
  {
    label: "Saved Jobs",
    href: "/saved",
    icon: Bookmark,
  },
  {
    label: "Applications",
    href: "/applications",
    icon: ClipboardCheck,
  },
  {
    label: "Notifications",
    href: "/notifications",
    icon: Bell,
  },
];

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    async function loadUnreadNotifications() {
      try {
        const notifications = await getNotifications(USER_ID);

        const unread = notifications.filter(
          (notification) =>
            notification.read_at === null,
        ).length;

        setUnreadCount(unread);
      } catch (error) {
        console.error(
          "Failed to load notification count:",
          error,
        );
      }
    }

    loadUnreadNotifications();
  }, []);

  const notificationBadge =
    unreadCount > 99 ? "99+" : unreadCount.toString();

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logoWrapper}>
          <div className={styles.logoMark}>J</div>

          <span className={styles.logoText}>
            JobForge
          </span>
        </div>

        <nav className={styles.navigation}>
          <p className={styles.sectionLabel}>
            Workspace
          </p>

          {navigation.map((item) => {
            const Icon = item.icon;

            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`${styles.navItem} ${
                  isActive
                    ? styles.navItemActive
                    : ""
                }`}
              >
                <Icon
                  size={19}
                  strokeWidth={1.8}
                />

                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className={styles.sidebarBottom}>
          <Link
            href="/profile"
            className={`${styles.navItem} ${
              pathname.startsWith("/profile")
                ? styles.navItemActive
                : ""
            }`}
          >
            <User
              size={19}
              strokeWidth={1.8}
            />

            <span>Career Profile</span>
          </Link>

          <Link
            href="/settings"
            className={`${styles.navItem} ${
              pathname.startsWith("/settings")
                ? styles.navItemActive
                : ""
            }`}
          >
            <Settings
              size={19}
              strokeWidth={1.8}
            />

            <span>Settings</span>
          </Link>
        </div>
      </aside>

      <div className={styles.mainArea}>
        <header className={styles.header}>
          <div>
            <p className={styles.headerLabel}>
              JobForge
            </p>

            <h1 className={styles.headerTitle}>
              Career workspace
            </h1>
          </div>

          <div className={styles.headerActions}>
            <Link
              href="/notifications"
              className={styles.notificationButton}
              aria-label={
                unreadCount > 0
                  ? `${unreadCount} unread notifications`
                  : "Notifications"
              }
            >
              <Bell
                size={20}
                strokeWidth={1.8}
              />

              {unreadCount > 0 && (
                <span
                  className={
                    styles.notificationBadge
                  }
                >
                  {notificationBadge}
                </span>
              )}
            </Link>

            <Link
              href="/profile"
              className={styles.profileButton}
              aria-label="Career profile"
            >
              <User
                size={19}
                strokeWidth={1.8}
              />
            </Link>
          </div>
        </header>

        <main className={styles.content}>
          {children}
        </main>
      </div>
    </div>
  );
}