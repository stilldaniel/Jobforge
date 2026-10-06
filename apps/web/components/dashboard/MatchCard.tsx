import Link from "next/link";
import {
  ArrowUpRight,
  Bookmark,
  Building2,
  MapPin,
} from "lucide-react";

import type { MatchedJob } from "@/types/api";

import { HIGH_MATCH_SCORE } from "@/lib/config";
import styles from "./MatchCard.module.css";

interface MatchCardProps {
  match: MatchedJob;
  isSaved: boolean;
  saving: boolean;
  onToggleSave: (match: MatchedJob) => void;
}

function getScoreClass(score: number) {
  if (score >= HIGH_MATCH_SCORE) {
    return styles.scoreHigh;
  }

  if (score >= 75) {
    return styles.scoreGood;
  }

  return styles.scoreAverage;
}

export default function MatchCard({
  match,
  isSaved,
  saving,
  onToggleSave,
}: MatchCardProps) {
  const reasons = match.match_reasons
    ? match.match_reasons
        .split(";")
        .map((reason) => reason.trim())
        .filter(Boolean)
        .slice(0, 3)
    : [];

  return (
    <article className={styles.card}>
      <div className={styles.main}>
        <div className={styles.companyIcon}>
          <Building2 size={20} strokeWidth={1.7} />
        </div>

        <div className={styles.details}>
          <div className={styles.titleRow}>
            <div>
              <h3 className={styles.title}>{match.title}</h3>

              <p className={styles.company}>
                {match.company}
              </p>
            </div>

            <div
              className={`${styles.score} ${getScoreClass(
                match.score,
              )}`}
            >
              {Math.round(match.score)}%
            </div>
          </div>

          <div className={styles.meta}>
            {match.location && (
              <span>
                <MapPin size={14} strokeWidth={1.7} />
                {match.location}
              </span>
            )}

            {match.work_type && (
              <span>{match.work_type}</span>
            )}
          </div>

          {reasons.length > 0 && (
            <div className={styles.reasons}>
              {reasons.map((reason) => (
                <span key={reason}>{reason}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={`${styles.saveButton} ${
            isSaved ? styles.saveButtonActive : ""
          }`}
          aria-label={
            isSaved
              ? `Remove ${match.title} from saved jobs`
              : `Save ${match.title}`
          }
          aria-pressed={isSaved}
          onClick={() => onToggleSave(match)}
          disabled={saving}
        >
          <Bookmark
            size={17}
            strokeWidth={1.8}
            fill={isSaved ? "currentColor" : "none"}
          />
        </button>

        <Link
          href={match.application_url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.applyButton}
        >
          Apply
          <ArrowUpRight size={16} strokeWidth={1.8} />
        </Link>
      </div>
    </article>
  );
}