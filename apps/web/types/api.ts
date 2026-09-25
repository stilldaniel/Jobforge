export interface User {
  id: number;
  email: string;
  full_name: string | null;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  full_name?: string | null;
  timezone?: string;
}

export interface CareerProfile {
  id: number;
  user_id: number;
  professional_title: string | null;
  years_of_experience: number;
  summary: string | null;
  skills: string | null;
  candidate_location: string | null;
  preferred_work_type: string | null;
  preferred_location: string | null;
  minimum_salary: number | null;
  maximum_salary: number | null;
  created_at: string;
  updated_at: string;
}

export interface CareerProfileCreate {
  professional_title?: string | null;
  skills?: string | null;
  years_of_experience?: number;
  summary?: string | null;
  candidate_location?: string | null;
  preferred_work_type?: string | null;
  preferred_location?: string | null;
  minimum_salary?: number | null;
  maximum_salary?: number | null;
}

export interface Job {
  id: number;
  title: string;
  company: string;
  description: string | null;
  location: string | null;
  work_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  application_url: string;
  source: string;
  fingerprint: string;
  posted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  title: string;
  company: string;
  description?: string | null;
  location?: string | null;
  work_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  application_url: string;
  source: string;
  posted_at?: string | null;
  required_skills?: string | null;
  required_experience?: number | null;
}

export interface MatchedJob {
  id: number;
  user_id: number;
  job_id: number;
  score: number;
  match_reasons: string | null;

  title: string;
  company: string;
  description: string | null;
  required_skills: string | null;
  required_experience: number | null;
  location: string | null;
  remote_eligibility: string | null;
  work_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  application_url: string;

  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  job_match_id: number;
  notification_type: string;
  channel: string;
  status: string;
  title: string;
  message: string | null;
  attempts: number;
  last_error: string | null;
  created_at: string;
  sent_at: string | null;
  read_at: string | null;
}

export interface DeleteResponse {
  message: string;
  user_id?: number;
  job_id?: number;
}

export interface JobDiscoveryResponse {
  message: string;
  jobs_found: number;
  jobs_updated: number;
  jobs: Job[];
  updated_jobs: Job[];
}

export interface NotificationCreationResponse {
  message: string;
  notifications_created: number;
  notifications: Array<{
    id: number;
    job_match_id: number;
    type: string;
    status: string;
    title: string;
    message: string | null;
  }>;
}

export interface MatchGenerationResponse {
  matches_created?: number;
  notifications_created?: number;
  jobs_found?: number;
  new_jobs?: number;
  updated_jobs?: number;
  source_errors?: string[];
}

export interface SavedJob {
  id: number;
  user_id: number;
  job_id: number;
  created_at: string;
  job: Job;
}

export interface SavedJobCreate {
  user_id: number;
  job_id: number;
}