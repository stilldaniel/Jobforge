"use client";

import {
  DEV_USER_ID as USER_ID,
  HIGH_MATCH_SCORE,
} from "@/lib/config";
import { FormEvent, useEffect, useState } from "react";
import {
  CheckCircle2,
  LoaderCircle,
  Save,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import {
  getNotificationPreferences,
  getUser,
  updateNotificationPreferences,
  updateUser,
} from "@/lib/api/users";

import type {
  NotificationPreferences,
  User,
  UserCreate,
} from "@/types/api";

import styles from "./page.module.css";


interface FormState {
  email: string;
  full_name: string;
  timezone: string;
}

const EMPTY_FORM: FormState = {
  email: "",
  full_name: "",
  timezone: "UTC",
};

type PreferenceKey = keyof NotificationPreferences;

interface PreferenceOption {
  key: PreferenceKey;
  label: string;
  description: string;
}

const PREFERENCE_OPTIONS: PreferenceOption[] = [
  {
    key: "job_alerts_enabled",
    label: "Job alerts",
    description:
      "Get notified about new jobs that match your career profile.",
  },
  {
    key: "email_notifications_enabled",
    label: "Email notifications",
    description:
      "Receive job alerts by email. When off, alerts still appear in JobForge.",
  },
  {
    key: "high_match_alerts_enabled",
    label: "Instant high-match emails",
    description: `Email me as soon as a job matches ${HIGH_MATCH_SCORE}% or higher. When off, these go into the daily digest.`,
  },
  {
    key: "digest_notifications_enabled",
    label: "Daily digest",
    description:
      "One email each morning with the other good matches found that day.",
  },
];

// Why a preference has no effect with the current settings, if it doesn't.
function disabledReason(
  key: PreferenceKey,
  preferences: NotificationPreferences,
): string | null {
  if (key === "job_alerts_enabled") {
    return null;
  }

  if (!preferences.job_alerts_enabled) {
    return "Turn on job alerts to use this.";
  }

  if (
    key !== "email_notifications_enabled" &&
    !preferences.email_notifications_enabled
  ) {
    return "Turn on email notifications to use this.";
  }

  return null;
}

// IANA timezone names offered as suggestions; the API rejects others.
const TIMEZONES: string[] =
  typeof Intl.supportedValuesOf === "function"
    ? Intl.supportedValuesOf("timeZone")
    : [];

function userToForm(user: User): FormState {
  return {
    email: user.email,
    full_name: user.full_name ?? "",
    timezone: user.timezone,
  };
}

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [form, setForm] =
    useState<FormState>(EMPTY_FORM);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [success, setSuccess] =
    useState<string | null>(null);

  const [preferences, setPreferences] =
    useState<NotificationPreferences | null>(null);

  const [savingPreference, setSavingPreference] =
    useState<PreferenceKey | null>(null);

  const [preferencesError, setPreferencesError] =
    useState<string | null>(null);

  const [preferencesSaved, setPreferencesSaved] =
    useState(false);

  useEffect(() => {
    async function loadUser() {
      try {
        setLoading(true);
        setError(null);

        const result = await getUser(USER_ID);

        setUser(result);
        setForm(userToForm(result));
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load your account settings.",
        );
      } finally {
        setLoading(false);
      }
    }

    async function loadPreferences() {
      try {
        setPreferences(
          await getNotificationPreferences(USER_ID),
        );
      } catch (err) {
        setPreferencesError(
          err instanceof Error
            ? err.message
            : "Failed to load your notification preferences.",
        );
      }
    }

    loadUser();
    loadPreferences();
  }, []);

  const togglePreference = async (key: PreferenceKey) => {
    if (!preferences || savingPreference) {
      return;
    }

    const previous = preferences;
    const value = !preferences[key];

    // Show the change straight away; undo it if saving fails.
    setPreferences({ ...preferences, [key]: value });
    setSavingPreference(key);
    setPreferencesError(null);
    setPreferencesSaved(false);

    try {
      const result = await updateNotificationPreferences(
        USER_ID,
        { [key]: value },
      );

      setPreferences(result);
      setPreferencesSaved(true);
    } catch (err) {
      setPreferences(previous);
      setPreferencesError(
        err instanceof Error
          ? err.message
          : "Failed to update your notification preferences.",
      );
    } finally {
      setSavingPreference(null);
    }
  };

  const updateField = (
    field: keyof FormState,
    value: string,
  ) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setSuccess(null);
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const payload: UserCreate = {
        email: form.email.trim(),
        full_name:
          form.full_name.trim() || null,
        timezone: form.timezone.trim() || "UTC",
      };

      const result = await updateUser(
        USER_ID,
        payload,
      );

      setUser(result);
      setForm(userToForm(result));

      setSuccess(
        "Your account settings have been updated.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update your account settings.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className={styles.loading}>
          <LoaderCircle
            size={21}
            className={styles.spinner}
          />
          <span>
            Loading your account settings...
          </span>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className={styles.page}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>
              Settings
            </p>

            <h1 className={styles.title}>
              Manage your account.
            </h1>

            <p className={styles.subtitle}>
              Update your account information and
              preferences used by JobForge.
            </p>
          </div>

          {user && (
            <div className={styles.accountStatus}>
              <CheckCircle2
                size={15}
                strokeWidth={1.8}
              />
              <span>Account active</span>
            </div>
          )}
        </header>

        {error && (
          <div className={styles.error}>
            <strong>
              Something went wrong.
            </strong>
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className={styles.success}>
            <CheckCircle2
              size={17}
              strokeWidth={1.8}
            />
            <span>{success}</span>
          </div>
        )}

        <form
          className={styles.form}
          onSubmit={handleSubmit}
        >
          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <p className={styles.cardEyebrow}>
                  Account
                </p>

                <h2 className={styles.cardTitle}>
                  Account information
                </h2>
              </div>

              <p className={styles.cardDescription}>
                Keep your basic account details
                up to date.
              </p>
            </div>

            <div className={styles.grid}>
              <div className={styles.field}>
                <label htmlFor="full_name">
                  Full name
                </label>

                <input
                  id="full_name"
                  type="text"
                  value={form.full_name}
                  onChange={(event) =>
                    updateField(
                      "full_name",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Daniel Ogundipe"
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="email">
                  Email address
                </label>

                <input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    updateField(
                      "email",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. daniel@example.com"
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="timezone">
                  Timezone
                </label>

                <input
                  id="timezone"
                  type="text"
                  value={form.timezone}
                  onChange={(event) =>
                    updateField(
                      "timezone",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Africa/Lagos"
                  list="timezone-options"
                  autoComplete="off"
                />

                <datalist id="timezone-options">
                  {TIMEZONES.map((name) => (
                    <option key={name} value={name} />
                  ))}
                </datalist>

                <span className={styles.hint}>
                  Your daily digest arrives each morning
                  in this timezone.
                </span>
              </div>
            </div>
          </section>

          <div className={styles.formFooter}>
            <p className={styles.footerHint}>
              Changes are saved to your JobForge
              account.
            </p>

            <button
              type="submit"
              className={styles.saveButton}
              disabled={saving}
            >
              {saving ? (
                <>
                  <LoaderCircle
                    size={16}
                    className={styles.spinner}
                  />
                  Saving...
                </>
              ) : (
                <>
                  <Save
                    size={16}
                    strokeWidth={1.8}
                  />
                  Save changes
                </>
              )}
            </button>
          </div>
        </form>

        <section
          className={styles.card}
          aria-labelledby="notification-preferences-title"
        >
          <div className={styles.cardHeader}>
            <div>
              <p className={styles.cardEyebrow}>
                Notifications
              </p>

              <h2
                id="notification-preferences-title"
                className={styles.cardTitle}
              >
                Notification preferences
              </h2>
            </div>

            <p
              className={styles.cardDescription}
              aria-live="polite"
            >
              {preferencesSaved
                ? "Saved."
                : "Changes are saved as soon as you switch them."}
            </p>
          </div>

          {preferencesError && (
            <div className={styles.error}>
              <strong>
                Couldn&apos;t update your preferences.
              </strong>
              <p>{preferencesError}</p>
            </div>
          )}

          {preferences && (
            <ul className={styles.preferenceList}>
              {PREFERENCE_OPTIONS.map((option) => {
                const checked = preferences[option.key];
                const reason = disabledReason(
                  option.key,
                  preferences,
                );
                const isSaving =
                  savingPreference === option.key;

                return (
                  <li
                    key={option.key}
                    className={`${styles.preference} ${
                      reason ? styles.preferenceInactive : ""
                    }`}
                  >
                    <div className={styles.preferenceText}>
                      <span
                        id={`${option.key}-label`}
                        className={styles.preferenceLabel}
                      >
                        {option.label}
                      </span>

                      <span
                        id={`${option.key}-description`}
                        className={styles.preferenceDescription}
                      >
                        {reason ?? option.description}
                      </span>
                    </div>

                    <button
                      type="button"
                      role="switch"
                      aria-checked={checked}
                      aria-labelledby={`${option.key}-label`}
                      aria-describedby={`${option.key}-description`}
                      className={`${styles.switch} ${
                        checked ? styles.switchOn : ""
                      }`}
                      onClick={() =>
                        togglePreference(option.key)
                      }
                      disabled={
                        Boolean(reason) ||
                        savingPreference !== null
                      }
                    >
                      <span className={styles.switchThumb}>
                        {isSaving && (
                          <LoaderCircle
                            size={10}
                            className={styles.spinner}
                          />
                        )}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </AppShell>
  );
}