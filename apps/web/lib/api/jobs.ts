import { api } from "./client";
import type { Job, JobCreate } from "@/types/api";

export function createJob(data: JobCreate) {
  return api.post<Job>("/jobs/", data);
}

export function getJobs() {
  return api.get<Job[]>("/jobs/");
}

export function getJob(jobId: number) {
  return api.get<Job>(`/jobs/${jobId}`);
}

export function updateJob(jobId: number, data: JobCreate) {
  return api.put<Job>(`/jobs/${jobId}`, data);
}

export function deleteJob(jobId: number) {
  return api.delete<{
    message: string;
    job_id: number;
  }>(`/jobs/${jobId}`);
}