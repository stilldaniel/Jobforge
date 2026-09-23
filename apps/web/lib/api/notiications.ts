import { api } from "./client";
import type { Notification } from "@/types/api";

export function getUserNotifications(userId: number) {
  return api.get<Notification[]>(
    `/notifications/${userId}`,
  );
}

export function markNotificationAsRead(
  notificationId: number,
) {
  return api.patch<Notification>(
    `/notifications/${notificationId}/read`,
  );
}

export function processDigestNotifications() {
  return api.post("/notifications/digest/process");
}