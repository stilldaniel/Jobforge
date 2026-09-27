import { api } from "@/lib/api/client";
import type {
  SavedJob,
  SavedJobCreate,
  Application,
  ApplicationCreate,
  ApplicationUpdate,
  DeleteResponse,
} from "@/types/api";

export function getSavedJobs(userId: number) {
  return api.get<SavedJob[]>(`/saved-jobs/${userId}`);
}

export function getSavedJob(userId: number, jobId: number) {
  return api.get<SavedJob>(
    `/saved-jobs/${userId}/${jobId}`,
  );
}

export function saveJob(data: SavedJobCreate) {
  return api.post<SavedJob>(
    "/saved-jobs/",
    data,
  );
}

export function unsaveJob(userId: number, jobId: number) {
  return api.delete<DeleteResponse>(
    `/saved-jobs/${userId}/${jobId}`,
  );
}

// Applications

export function getApplications(userId: number) {
  return api.get<Application[]>(
    `/applications/${userId}`,
  );
}

export function getApplication(userId: number, jobId: number) {
  return api.get<Application>(
    `/applications/${userId}/${jobId}`,
  );
}

export function createApplication(data: ApplicationCreate) {
  return api.post<Application>(
    "/applications/",
    data,
  );
}

export function updateApplication(
  userId: number,
  jobId: number,
  data: ApplicationUpdate,
) {
  return api.patch<Application>(
    `/applications/${userId}/${jobId}`,
    data,
  );
}

export function deleteApplication(
  userId: number,
  jobId: number,
) {
  return api.delete<DeleteResponse>(
    `/applications/${userId}/${jobId}`,
  );
}