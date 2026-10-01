import {
  BriefcaseBusiness,
  CheckCircle2,
  CircleX,
  FileCheck2,
  MessageSquareText,
} from "lucide-react";

import type { Application } from "@/types/api";

import styles from "./ApplicationPipeline.module.css";

interface ApplicationPipelineProps {
  applications: Application[];
}

const PIPELINE_STATUSES = [
  {
    status: "applied",
    label: "Applied",
    description: "Applications submitted",
    icon: BriefcaseBusiness,
  },
  {
    status: "interview",
    label: "Interview",
    description: "Interview stage",
    icon: MessageSquareText,
  },
  {
    status: "offer",
    label: "Offer",
    description: "Offers received",
    icon: FileCheck2,
  },
  {
    status: "rejected",
    label: "Rejected",
    description: "Applications rejected",
    icon: CircleX,
  },
  {
    status: "withdrawn",
    label: "Withdrawn",
    description: "Applications withdrawn",
    icon: CheckCircle2,
  },
] as const;

export default function ApplicationPipeline({
  applications,
}: ApplicationPipelineProps) {
  return (
    <section className={styles.pipeline}>
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Application tracking</p>

          <h2 className={styles.title}>
            Application pipeline
          </h2>
        </div>

        <span className={styles.total}>
          {applications.length}{" "}
          {applications.length === 1
            ? "application"
            : "applications"}
        </span>
      </div>

      <div className={styles.steps}>
        {PIPELINE_STATUSES.map((item) => {
          const Icon = item.icon;

          const count = applications.filter(
            (application) =>
              application.status === item.status,
          ).length;

          return (
            <div
              key={item.status}
              className={styles.step}
            >
              <div className={styles.icon}>
                <Icon
                  size={17}
                  strokeWidth={1.8}
                />
              </div>

              <div className={styles.stepContent}>
                <div className={styles.stepTop}>
                  <span className={styles.label}>
                    {item.label}
                  </span>

                  <span className={styles.count}>
                    {count}
                  </span>
                </div>

                <p className={styles.description}>
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}