import { api } from "./client";
import type {
  DeleteResponse,
  User,
  UserCreate,
} from "@/types/api";

export function createUser(data: UserCreate) {
  return api.post<User>("/users/", data);
}

export function getUsers() {
  return api.get<User[]>("/users/");
}

export function getUser(userId: number) {
  return api.get<User>(`/users/${userId}`);
}

export function updateUser(userId: number, data: UserCreate) {
  return api.put<User>(`/users/${userId}`, data);
}

export function deleteUser(userId: number) {
  return api.delete<DeleteResponse>(`/users/${userId}`);
}