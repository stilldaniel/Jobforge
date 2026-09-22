import { api } from "./client";
import type {
  JobDiscoveryResponse,
  MatchGenerationResponse,
} from "@/types/api";

export function runJobDiscovery() {
  return api.post<JobDiscoveryResponse>(
    "/job-discovery/run",
  );
}

export function runJobMonitor() {
  return api.post<MatchGenerationResponse>(
    "/job-discovery/monitor",
  );
}