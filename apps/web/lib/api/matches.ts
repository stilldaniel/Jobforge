import { api } from "./client";
import type {
  MatchedJob,
  NotificationCreationResponse,
} from "@/types/api";

export function generateMatches(userId: number) {
  return api.post<MatchedJob[]>(
    `/matches/${userId}/generate`,
  );
}

export function getUserMatches(userId: number) {
  return api.get<MatchedJob[]>(
    `/matches/${userId}`,
  );
}

export function createMatchNotifications(userId: number) {
  return api.post<NotificationCreationResponse>(
    `/matches/${userId}/notifications`,
  );
}