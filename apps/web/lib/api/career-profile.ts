import { api } from "./client";
import type {
  CareerProfile,
  CareerProfileCreate,
} from "@/types/api";

export function createCareerProfile(
  userId: number,
  data: CareerProfileCreate,
) {
  return api.post<CareerProfile>(
    `/users/${userId}/career-profile/`,
    data,
  );
}

export function getCareerProfile(userId: number) {
  return api.get<CareerProfile>(
    `/users/${userId}/career-profile/`,
  );
}

export function updateCareerProfile(
  userId: number,
  data: CareerProfileCreate,
) {
  return api.put<CareerProfile>(
    `/users/${userId}/career-profile/`,
    data,
  );
}