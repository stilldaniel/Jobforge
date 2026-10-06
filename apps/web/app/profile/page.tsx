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
  createCareerProfile,
  getCareerProfile,
  updateCareerProfile,
} from "@/lib/api/career-profile";

import type {
  CareerProfile,
  CareerProfileCreate,
} from "@/types/api";

import styles from "./page.module.css";


const WORK_TYPES = [
  {
    value: "",
    label: "Select work type",
  },
  {
    value: "remote",
    label: "Remote",
  },
  {
    value: "hybrid",
    label: "Hybrid",
  },
  {
    value: "onsite",
    label: "On-site",
  },
];

interface FormState {
  professional_title: string;
  years_of_experience: string;
  summary: string;
  skills: string;
  candidate_location: string;
  preferred_work_type: string;
  preferred_location: string;
  minimum_salary: string;
  maximum_salary: string;
  salary_currency: string;
  salary_period: "month" | "year";
}

// Job salaries are compared only in the same currency.
const SALARY_CURRENCIES = [
  { value: "", label: "Not set" },
  { value: "USD", label: "USD – US dollar" },
  { value: "EUR", label: "EUR – Euro" },
  { value: "GBP", label: "GBP – British pound" },
  { value: "CAD", label: "CAD – Canadian dollar" },
  { value: "AUD", label: "AUD – Australian dollar" },
  { value: "NGN", label: "NGN – Nigerian naira" },
  { value: "GHS", label: "GHS – Ghanaian cedi" },
  { value: "KES", label: "KES – Kenyan shilling" },
  { value: "ZAR", label: "ZAR – South African rand" },
  { value: "INR", label: "INR – Indian rupee" },
];

const EMPTY_FORM: FormState = {
  professional_title: "",
  years_of_experience: "0",
  summary: "",
  skills: "",
  candidate_location: "",
  preferred_work_type: "",
  preferred_location: "",
  minimum_salary: "",
  maximum_salary: "",
  salary_currency: "",
  salary_period: "month",
};

function formatSkillsForForm(
  skills: string | null,
): string {
  if (!skills) {
    return "";
  }

  try {
    const parsed = JSON.parse(skills);

    if (Array.isArray(parsed)) {
      return parsed
        .filter(
          (skill): skill is string =>
            typeof skill === "string",
        )
        .join(", ");
    }
  } catch {
    // Fall back to the raw value if it isn't JSON.
  }

  return skills;
}

function profileToForm(
  profile: CareerProfile,
): FormState {
  return {
    professional_title:
      profile.professional_title ?? "",

    years_of_experience:
      profile.years_of_experience.toString(),

    summary: profile.summary ?? "",

    skills: formatSkillsForForm(profile.skills),

    candidate_location:
      profile.candidate_location ?? "",

    preferred_work_type:
      profile.preferred_work_type ?? "",

    preferred_location:
      profile.preferred_location ?? "",

    minimum_salary:
      profile.minimum_salary?.toString() ?? "",

    maximum_salary:
      profile.maximum_salary?.toString() ?? "",

    salary_currency: profile.salary_currency ?? "",

    salary_period: profile.salary_period ?? "month",
  };
}

export default function ProfilePage() {
  const [form, setForm] =
    useState<FormState>(EMPTY_FORM);

  const [profile, setProfile] =
    useState<CareerProfile | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [success, setSuccess] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError(null);

        const result =
          await getCareerProfile(USER_ID);

        setProfile(result);
        setForm(profileToForm(result));
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed to load your career profile.";

        if (
          message
            .toLowerCase()
            .includes("not found")
        ) {
          setProfile(null);
          setForm(EMPTY_FORM);
        } else {
          setError(message);
        }
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
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

      const payload: CareerProfileCreate = {
        professional_title:
          form.professional_title.trim() || null,

        years_of_experience:
          Number(form.years_of_experience) || 0,

        summary:
          form.summary.trim() || null,

        skills: form.skills.trim()
          ? JSON.stringify(
              form.skills
                .split(",")
                .map((skill) => skill.trim())
                .filter(Boolean),
            )
          : null,

        candidate_location:
          form.candidate_location.trim() || null,

        preferred_work_type:
          form.preferred_work_type || null,

        preferred_location:
          form.preferred_location.trim() || null,

        minimum_salary:
          form.minimum_salary.trim()
            ? Number(form.minimum_salary)
            : null,

        maximum_salary:
          form.maximum_salary.trim()
            ? Number(form.maximum_salary)
            : null,

        salary_currency:
          form.salary_currency || null,

        salary_period: form.salary_currency
          ? form.salary_period
          : null,
      };

      const result = profile
        ? await updateCareerProfile(
            USER_ID,
            payload,
          )
        : await createCareerProfile(
            USER_ID,
            payload,
          );

      setProfile(result);
      setForm(profileToForm(result));

      setSuccess(
        profile
          ? "Your career profile has been updated and your job matches re-scored."
          : "Your career profile has been created and your job matches scored.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to save your career profile.",
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
            Loading your career profile...
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
              Career profile
            </p>

            <h1 className={styles.title}>
              Tell JobForge about your career.
            </h1>

            <p className={styles.subtitle}>
              Your profile helps JobForge understand
              what you&apos;re looking for and match you
              with relevant opportunities.
            </p>
          </div>

          {profile && (
            <div className={styles.profileStatus}>
              <CheckCircle2
                size={15}
                strokeWidth={1.8}
              />

              <span>Profile active</span>
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
                  About you
                </p>

                <h2 className={styles.cardTitle}>
                  Professional background
                </h2>
              </div>

              <p className={styles.cardDescription}>
                Give JobForge enough context to
                understand your experience.
              </p>
            </div>

            <div className={styles.grid}>
              <div className={styles.field}>
                <label htmlFor="professional_title">
                  Professional title
                </label>

                <input
                  id="professional_title"
                  type="text"
                  value={form.professional_title}
                  onChange={(event) =>
                    updateField(
                      "professional_title",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Full-stack Software Developer"
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="years_of_experience">
                  Years of experience
                </label>

                <input
                  id="years_of_experience"
                  type="number"
                  min="0"
                  step="0.5"
                  value={form.years_of_experience}
                  onChange={(event) =>
                    updateField(
                      "years_of_experience",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. 5"
                />
              </div>

              <div
                className={`${styles.field} ${styles.fullWidth}`}
              >
                <label htmlFor="summary">
                  Professional summary
                </label>

                <textarea
                  id="summary"
                  value={form.summary}
                  onChange={(event) =>
                    updateField(
                      "summary",
                      event.target.value,
                    )
                  }
                  placeholder="Briefly describe your professional background, strengths, and the kind of work you do."
                  rows={5}
                />

                <span className={styles.hint}>
                  Keep this focused on your experience,
                  strengths, and professional direction.
                </span>
              </div>

              <div
                className={`${styles.field} ${styles.fullWidth}`}
              >
                <label htmlFor="skills">
                  Skills
                </label>

                <textarea
                  id="skills"
                  value={form.skills}
                  onChange={(event) =>
                    updateField(
                      "skills",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. React, Next.js, TypeScript, Node.js, PostgreSQL, AWS"
                  rows={3}
                />

                <span className={styles.hint}>
                  Separate skills with commas.
                </span>
              </div>
            </div>
          </section>

          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <p className={styles.cardEyebrow}>
                  Preferences
                </p>

                <h2 className={styles.cardTitle}>
                  What are you looking for?
                </h2>
              </div>

              <p className={styles.cardDescription}>
                These preferences influence how jobs
                are matched to your profile.
              </p>
            </div>

            <div className={styles.grid}>
              <div className={styles.field}>
                <label htmlFor="candidate_location">
                  Current location
                </label>

                <input
                  id="candidate_location"
                  type="text"
                  value={form.candidate_location}
                  onChange={(event) =>
                    updateField(
                      "candidate_location",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Lagos, Nigeria"
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="preferred_work_type">
                  Preferred work type
                </label>

                <select
                  id="preferred_work_type"
                  value={form.preferred_work_type}
                  onChange={(event) =>
                    updateField(
                      "preferred_work_type",
                      event.target.value,
                    )
                  }
                >
                  {WORK_TYPES.map((type) => (
                    <option
                      key={type.value}
                      value={type.value}
                    >
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className={styles.field}>
                <label htmlFor="preferred_location">
                  Preferred location
                </label>

                <input
                  id="preferred_location"
                  type="text"
                  value={form.preferred_location}
                  onChange={(event) =>
                    updateField(
                      "preferred_location",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Remote, Lagos, Europe"
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="minimum_salary">
                  Minimum salary
                </label>

                <input
                  id="minimum_salary"
                  type="number"
                  min="0"
                  step="1"
                  value={form.minimum_salary}
                  onChange={(event) =>
                    updateField(
                      "minimum_salary",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. 3000"
                />

                <span className={styles.hint}>
                  Shown next to each job&apos;s pay for
                  reference. Pay never filters out a job.
                </span>
              </div>

              <div className={styles.field}>
                <label htmlFor="maximum_salary">
                  Maximum salary
                </label>

                <input
                  id="maximum_salary"
                  type="number"
                  min="0"
                  step="1"
                  value={form.maximum_salary}
                  onChange={(event) =>
                    updateField(
                      "maximum_salary",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. 6000"
                />
              </div>

              <div className={styles.field}>
                <label htmlFor="salary_currency">
                  Salary currency
                </label>

                <select
                  id="salary_currency"
                  value={form.salary_currency}
                  onChange={(event) =>
                    updateField(
                      "salary_currency",
                      event.target.value,
                    )
                  }
                >
                  {SALARY_CURRENCIES.map((currency) => (
                    <option
                      key={currency.value}
                      value={currency.value}
                    >
                      {currency.label}
                    </option>
                  ))}
                </select>

                <span className={styles.hint}>
                  Pay is compared only for jobs in this
                  currency.
                </span>
              </div>

              <div className={styles.field}>
                <label htmlFor="salary_period">
                  Salary period
                </label>

                <select
                  id="salary_period"
                  value={form.salary_period}
                  disabled={!form.salary_currency}
                  onChange={(event) =>
                    updateField(
                      "salary_period",
                      event.target.value,
                    )
                  }
                >
                  <option value="month">Per month</option>
                  <option value="year">Per year</option>
                </select>
              </div>
            </div>
          </section>

          <div className={styles.formFooter}>
            <p className={styles.footerHint}>
              Keep your profile updated so your job
              matches stay relevant.
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

                  {profile
                    ? "Save changes"
                    : "Create profile"}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </AppShell>
  );
}