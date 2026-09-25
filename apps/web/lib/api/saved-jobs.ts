import { api } from "@/lib/api/client";
import type {
  SavedJob,
  SavedJobCreate,
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