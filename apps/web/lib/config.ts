// Temporary until authentication exists: every page acts as this user.
export const DEV_USER_ID = Number(
  process.env.NEXT_PUBLIC_DEV_USER_ID || "5",
);

// Matches at or above this score are emailed instantly by the API
// (IMMEDIATE_NOTIFICATION_SCORE) and shown as high matches here.
export const HIGH_MATCH_SCORE = 89;

// Public portfolio demo: the app runs on built-in sample data and never
// calls the backend. Set NEXT_PUBLIC_DEMO_MODE=true when building it.
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
