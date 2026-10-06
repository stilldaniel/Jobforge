"use client";

import { DEV_USER_ID as USER_ID } from "@/lib/config";
import { FormEvent, useEffect, useState } from "react";
import {
  CheckCircle2,
  LoaderCircle,
  Save,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import {
  getUser,
  updateUser,
} from "@/lib/api/users";

import type {
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

    loadUser();
  }, []);

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
                />

                <span className={styles.hint}>
                  Used when displaying dates and
                  scheduling job notifications.
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
      </div>
    </AppShell>
  );
}