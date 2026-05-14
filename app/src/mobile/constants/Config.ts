import Constants from "expo-constants";

/**
 * Standard configuration management for Mobile apps.
 * Uses EXPO_PUBLIC_ prefix for environment variables to be accessible in client-side code.
 */
export const Config = {
  ALLOWED_DOMAIN: process.env.EXPO_PUBLIC_ALLOWED_DOMAIN || "attono.net",
  API_URL: process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000",
  GOOGLE_ANDROID_CLIENT_ID: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || "",
  GOOGLE_IOS_CLIENT_ID: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || "",
  GOOGLE_WEB_CLIENT_ID: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || "",
};
