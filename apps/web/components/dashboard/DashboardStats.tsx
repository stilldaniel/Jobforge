import {
  Bell,
  BriefcaseBusiness,
  Sparkles,
  UserRound,
} from "lucide-react";

import styles from "./DashboardStats.module.css";

interface DashboardStatsProps {
  totalMatches: number;
  highMatches: number;
  unreadNotifications: number;
  profileComplete: boolean;
}

export default function DashboardStats({
  totalMatches,
  highMatches,
  unreadNotifications,
  profileComplete,
}: DashboardStatsProps) {
  const stats = [
    {
      label: "Total Matches",
      value: totalMatches,
      description: "Jobs matched to your profile",
      icon: BriefcaseBusiness,
    },
    {
      label: "High Matches",
      value: highMatches,
      description: "91% match or higher",
      icon: Sparkles,
    },
    {
      label: "Unread Notifications",
      value: unreadNotifications,
      description: "Notifications waiting for you",
      icon: Bell,
    },
    {
      label: "Career Profile",
      value: profileComplete ? "Ready" : "Setup",
      description: profileComplete
        ? "Your profile is available"
        : "Complete your profile",
      icon: UserRound,
    },
  ];

  return (
    <section className={styles.grid}>
      {stats.map((stat) => {
        const Icon = stat.icon;

        return (
          <div key={stat.label} className={styles.card}>
            <div className={styles.topRow}>
              <div className={styles.icon}>
                <Icon size={18} strokeWidth={1.8} />
              </div>
            </div>

            <div className={styles.value}>{stat.value}</div>

            <div className={styles.label}>{stat.label}</div>

            <p className={styles.description}>
              {stat.description}
            </p>
          </div>
        );
      })}
    </section>
  );
}