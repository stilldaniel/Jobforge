"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ChevronDown,
  LoaderCircle,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import { getJobs } from "@/lib/api/jobs";
import { getUserMatches } from "@/lib/api/matches";

import type { Job, MatchedJob } from "@/types/api";

import styles from "./page.module.css";

const USER_ID = Number(process.env.NEXT_PUBLIC_DEV_USER_ID || "3");

type SortOption = "newest" | "highest-match" | "salary";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matches, setMatches] = useState<MatchedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [locationFilter, setLocationFilter] = useState("all");
  const [workTypeFilter, setWorkTypeFilter] = useState("all");
  const [matchFilter, setMatchFilter] = useState("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [filtersOpen, setFiltersOpen] = useState(false);

  useEffect(() => {
    async function loadJobs() {
      try {
        setLoading(true);
        setError(null);

        const [jobsResult, matchesResult] = await Promise.all([
          getJobs(),
          getUserMatches(USER_ID),
        ]);

        setJobs(jobsResult);
        setMatches(matchesResult);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load jobs.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadJobs();
  }, []);

  const matchMap = useMemo(() => {
    return new Map(matches.map((match) => [match.job_id, match]));
  }, [matches]);

  const locations = useMemo(() => {
    return Array.from(
      new Set(
        jobs
          .map((job) => job.location)
          .filter((location): location is string => Boolean(location)),
      ),
    ).sort();
  }, [jobs]);

  const workTypes = useMemo(() => {
    return Array.from(
      new Set(
        jobs
          .map((job) => job.work_type)
          .filter((workType): workType is string => Boolean(workType)),
      ),
    ).sort();
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    const result = jobs.filter((job) => {
      const matchesSearch =
        !normalizedSearch ||
        job.title.toLowerCase().includes(normalizedSearch) ||
        job.company.toLowerCase().includes(normalizedSearch) ||
        (job.description ?? "").toLowerCase().includes(normalizedSearch);

      const matchesLocation =
        locationFilter === "all" ||
        job.location === locationFilter;

      const matchesWorkType =
        workTypeFilter === "all" ||
        job.work_type === workTypeFilter;

      const match = matchMap.get(job.id);

      const matchesScore =
        matchFilter === "all" ||
        (matchFilter === "high" && match && match.score >= 91) ||
        (matchFilter === "good" &&
          match &&
          match.score >= 75 &&
          match.score < 91) ||
        (matchFilter === "any" && Boolean(match));

      return (
        matchesSearch &&
        matchesLocation &&
        matchesWorkType &&
        matchesScore
      );
    });

    return result.sort((a, b) => {
      const matchA = matchMap.get(a.id);
      const matchB = matchMap.get(b.id);

      if (sortBy === "highest-match") {
        return (matchB?.score ?? -1) - (matchA?.score ?? -1);
      }

      if (sortBy === "salary") {
        return (
          (b.salary_max ?? b.salary_min ?? 0) -
          (a.salary_max ?? a.salary_min ?? 0)
        );
      }

      const dateA = a.posted_at
        ? new Date(a.posted_at).getTime()
        : new Date(a.created_at).getTime();

      const dateB = b.posted_at
        ? new Date(b.posted_at).getTime()
        : new Date(b.created_at).getTime();

      return dateB - dateA;
    });
  }, [
    jobs,
    search,
    locationFilter,
    workTypeFilter,
    matchFilter,
    sortBy,
    matchMap,
  ]);

  const hasActiveFilters =
    search.trim() !== "" ||
    locationFilter !== "all" ||
    workTypeFilter !== "all" ||
    matchFilter !== "all";

  function clearFilters() {
    setSearch("");
    setLocationFilter("all");
    setWorkTypeFilter("all");
    setMatchFilter("all");
    setSortBy("newest");
  }

  return (
    <AppShell>
      <div className={styles.page}>
        <section className={styles.hero}>
          <div>
            <p className={styles.eyebrow}>Jobs</p>

            <h2 className={styles.heading}>
              Find your next opportunity.
            </h2>

            <p className={styles.subtitle}>
              Explore jobs discovered by JobForge and see how well
              they match your career profile.
            </p>
          </div>

          <Link href="/" className={styles.backButton}>
            Dashboard
            <ArrowRight size={16} strokeWidth={1.8} />
          </Link>
        </section>

        {loading ? (
          <div className={styles.loading}>
            <LoaderCircle
              size={20}
              className={styles.spinner}
            />
            <span>Loading jobs...</span>
          </div>
        ) : error ? (
          <div className={styles.error}>
            <strong>Unable to load jobs.</strong>
            <p>{error}</p>
          </div>
        ) : (
          <>
            <section className={styles.toolbar}>
              <div className={styles.searchWrapper}>
                <Search
                  size={17}
                  strokeWidth={1.8}
                  className={styles.searchIcon}
                />

                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search jobs, companies, or keywords..."
                  className={styles.searchInput}
                />
              </div>

              <button
                type="button"
                onClick={() => setFiltersOpen((open) => !open)}
                className={`${styles.filterIcon} ${
                  filtersOpen ? styles.filterIconActive : ""
                }`}
                aria-label="Open filters"
                aria-expanded={filtersOpen}
              >
                <SlidersHorizontal
                  size={17}
                  strokeWidth={1.8}
                />
              </button>

              <div className={styles.selectWrapper}>
                <select
                  value={locationFilter}
                  onChange={(event) =>
                    setLocationFilter(event.target.value)
                  }
                  className={styles.select}
                >
                  <option value="all">All locations</option>

                  {locations.map((location) => (
                    <option key={location} value={location}>
                      {location}
                    </option>
                  ))}
                </select>

                <ChevronDown
                  size={15}
                  className={styles.selectIcon}
                />
              </div>

              <div className={styles.selectWrapper}>
                <select
                  value={workTypeFilter}
                  onChange={(event) =>
                    setWorkTypeFilter(event.target.value)
                  }
                  className={styles.select}
                >
                  <option value="all">All work types</option>

                  {workTypes.map((workType) => (
                    <option key={workType} value={workType}>
                      {workType}
                    </option>
                  ))}
                </select>

                <ChevronDown
                  size={15}
                  className={styles.selectIcon}
                />
              </div>

              <div className={styles.selectWrapper}>
                <select
                  value={matchFilter}
                  onChange={(event) =>
                    setMatchFilter(event.target.value)
                  }
                  className={styles.select}
                >
                  <option value="all">All matches</option>
                  <option value="high">High match · 91%+</option>
                  <option value="good">Good match · 75–90%</option>
                  <option value="any">Matched jobs only</option>
                </select>

                <ChevronDown
                  size={15}
                  className={styles.selectIcon}
                />
              </div>

              <div className={styles.selectWrapper}>
                <select
                  value={sortBy}
                  onChange={(event) =>
                    setSortBy(event.target.value as SortOption)
                  }
                  className={styles.select}
                >
                  <option value="newest">Newest</option>
                  <option value="highest-match">
                    Highest match
                  </option>
                  <option value="salary">Highest salary</option>
                </select>

                <ChevronDown
                  size={15}
                  className={styles.selectIcon}
                />
              </div>
            </section>

            {filtersOpen && (
              <section className={styles.filterPanel}>
                <div className={styles.filterPanelHeader}>
                  <div>
                    <p className={styles.filterPanelEyebrow}>
                      Filters
                    </p>

                    <h3 className={styles.filterPanelTitle}>
                      Refine your job search
                    </h3>
                  </div>

                  <button
                    type="button"
                    onClick={clearFilters}
                    className={styles.panelClearButton}
                  >
                    Clear all
                  </button>
                </div>

                <div className={styles.filterGrid}>
                  <label className={styles.filterField}>
                    <span>Location</span>

                    <select
                      value={locationFilter}
                      onChange={(event) =>
                        setLocationFilter(event.target.value)
                      }
                      className={styles.panelSelect}
                    >
                      <option value="all">All locations</option>

                      {locations.map((location) => (
                        <option key={location} value={location}>
                          {location}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className={styles.filterField}>
                    <span>Work type</span>

                    <select
                      value={workTypeFilter}
                      onChange={(event) =>
                        setWorkTypeFilter(event.target.value)
                      }
                      className={styles.panelSelect}
                    >
                      <option value="all">All work types</option>

                      {workTypes.map((workType) => (
                        <option key={workType} value={workType}>
                          {workType}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className={styles.filterField}>
                    <span>Match quality</span>

                    <select
                      value={matchFilter}
                      onChange={(event) =>
                        setMatchFilter(event.target.value)
                      }
                      className={styles.panelSelect}
                    >
                      <option value="all">All matches</option>
                      <option value="high">
                        High match · 91%+
                      </option>
                      <option value="good">
                        Good match · 75–90%
                      </option>
                      <option value="any">
                        Matched jobs only
                      </option>
                    </select>
                  </label>

                  <label className={styles.filterField}>
                    <span>Sort by</span>

                    <select
                      value={sortBy}
                      onChange={(event) =>
                        setSortBy(
                          event.target.value as SortOption,
                        )
                      }
                      className={styles.panelSelect}
                    >
                      <option value="newest">Newest</option>
                      <option value="highest-match">
                        Highest match
                      </option>
                      <option value="salary">
                        Highest salary
                      </option>
                    </select>
                  </label>
                </div>
              </section>
            )}

            <section className={styles.jobsSection}>
              <div className={styles.sectionHeader}>
                <div>
                  <p className={styles.sectionEyebrow}>
                    Opportunities
                  </p>

                  <h2 className={styles.sectionTitle}>
                    Available jobs
                  </h2>
                </div>

                <div className={styles.resultInfo}>
                  <span>
                    {filteredJobs.length}{" "}
                    {filteredJobs.length === 1
                      ? "job"
                      : "jobs"}
                  </span>

                  {hasActiveFilters && (
                    <button
                      type="button"
                      onClick={clearFilters}
                      className={styles.clearButton}
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              </div>

              {filteredJobs.length === 0 ? (
                <div className={styles.empty}>
                  <h3>No jobs match your filters</h3>

                  <p>
                    Try changing your search or removing one or
                    more filters.
                  </p>

                  <button
                    type="button"
                    onClick={clearFilters}
                    className={styles.emptyButton}
                  >
                    Clear filters
                  </button>
                </div>
              ) : (
                <div className={styles.jobList}>
                  {filteredJobs.map((job) => {
                    const match = matchMap.get(job.id);

                    return (
                      <article
                        key={job.id}
                        className={styles.jobCard}
                      >
                        <div className={styles.jobMain}>
                          <div className={styles.jobHeader}>
                            <div>
                              <p className={styles.company}>
                                {job.company}
                              </p>

                              <h3 className={styles.jobTitle}>
                                {job.title}
                              </h3>
                            </div>

                            {match && (
                              <div className={styles.score}>
                                {Math.round(match.score)}%
                                <span>match</span>
                              </div>
                            )}
                          </div>

                          <div className={styles.meta}>
                            {job.location && (
                              <span>{job.location}</span>
                            )}

                            {job.work_type && (
                              <span>{job.work_type}</span>
                            )}

                            {(job.salary_min !== null ||
                              job.salary_max !== null) && (
                              <span>
                                {job.salary_min !== null
                                  ? `$${job.salary_min.toLocaleString()}`
                                  : ""}
                                {job.salary_min !== null &&
                                job.salary_max !== null
                                  ? " – "
                                  : ""}
                                {job.salary_max !== null
                                  ? `$${job.salary_max.toLocaleString()}`
                                  : ""}
                              </span>
                            )}
                          </div>

                          {match?.match_reasons && (
                            <div className={styles.reasons}>
                              {match.match_reasons
                                .split(";")
                                .map((reason) => reason.trim())
                                .filter(Boolean)
                                .map((reason, index) => (
                                  <span
                                    key={`${match.id}-${index}`}
                                    className={styles.reason}
                                  >
                                    {reason}
                                  </span>
                                ))}
                            </div>
                          )}
                        </div>

                        <div className={styles.jobActions}>
                          <a
                            href={job.application_url}
                            target="_blank"
                            rel="noreferrer"
                            className={styles.applyButton}
                          >
                            Apply
                            <ArrowRight
                              size={15}
                              strokeWidth={1.8}
                            />
                          </a>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}