import { api } from "@/lib/api/client";
import type { Notification } from "@/types/api";

export function getNotifications(userId: number) {
  return api.get<Notification[]>(`/notifications/${userId}`);
}

export function markNotificationAsRead(notificationId: number) {
  return api.patch<Notification>(
    `/notifications/${notificationId}/read`,
  );
}