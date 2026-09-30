import {
  Bell,
  BriefcaseBusiness,
  CheckCircle2,
  MessageSquareText,
  Sparkles,
  Trophy,
} from "lucide-react";

import styles from "./DashboardStats.module.css";

interface DashboardStatsProps {
  totalMatches: number;
  highMatches: number;
  applications: number;
  interviews: number;
  offers: number;
  unreadNotifications: number;
}

export default function DashboardStats({
  totalMatches,
  highMatches,
  applications,
  interviews,
  offers,
  unreadNotifications,
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
      label: "Applications",
      value: applications,
      description: "Jobs you've applied to",
      icon: MessageSquareText,
    },
    {
      label: "Interviews",
      value: interviews,
      description: "Applications in interview stage",
      icon: CheckCircle2,
    },
    {
      label: "Offers",
      value: offers,
      description: "Applications with offers",
      icon: Trophy,
    },
    {
      label: "Unread Notifications",
      value: unreadNotifications,
      description: "Notifications waiting for you",
      icon: Bell,
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