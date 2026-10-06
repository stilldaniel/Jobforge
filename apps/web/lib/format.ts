import type { Job } from "@/types/api";

type SalaryFields = Pick<
  Job,
  "salary_min" | "salary_max" | "salary_currency" | "salary_period"
>;

const PERIOD_SUFFIXES: Record<string, string> = {
  year: "/yr",
  month: "/mo",
};

function formatAmount(
  amount: number,
  currency: string | null,
): string {
  if (!currency) {
    return amount.toLocaleString();
  }

  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    // Unknown currency code: show it next to the number.
    return `${currency} ${amount.toLocaleString()}`;
  }
}

export function formatSalary(job: SalaryFields): string | null {
  const { salary_min: min, salary_max: max } = job;

  if (min === null && max === null) {
    return null;
  }

  const currency = job.salary_currency ?? null;
  const suffix = job.salary_period
    ? (PERIOD_SUFFIXES[job.salary_period] ?? "")
    : "";

  if (min !== null && max !== null) {
    return `${formatAmount(min, currency)} – ${formatAmount(max, currency)}${suffix}`;
  }

  if (min !== null) {
    return `From ${formatAmount(min, currency)}${suffix}`;
  }

  return `Up to ${formatAmount(max as number, currency)}${suffix}`;
}

// Several platforms require their name to be shown as the job's source.
const SOURCE_NAMES: Record<string, string> = {
  adzuna: "Adzuna",
  arbeitnow: "Arbeitnow",
  ashby: "Ashby",
  greenhouse: "Greenhouse",
  himalayas: "Himalayas",
  jobicy: "Jobicy",
  lever: "Lever",
  manual: "Added manually",
  mock: "Sample data",
  remoteok: "Remote OK",
  remotive: "Remotive",
  weworkremotely: "We Work Remotely",
};

export function formatSource(source: string): string {
  return SOURCE_NAMES[source] ?? source;
}
