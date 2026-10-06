// Temporary until authentication exists: every page acts as this user.
export const DEV_USER_ID = Number(
  process.env.NEXT_PUBLIC_DEV_USER_ID || "5",
);
