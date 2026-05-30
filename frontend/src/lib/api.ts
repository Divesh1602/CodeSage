import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        window.location.href = "/";
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  githubCallback: (code: string) =>
    api.post<{ access_token: string; user: User }>("/auth/github/callback", null, {
      params: { code },
    }),
  getMe: () => api.get<User>("/auth/me"),
};

// Repositories
export const reposApi = {
  list: () => api.get<Repository[]>("/repositories"),
  sync: () => api.post<{ synced: number; repositories: Repository[] }>("/repositories/sync"),
  toggle: (repoId: string, enabled: boolean) =>
    api.patch<Repository>(`/repositories/${repoId}/toggle`, { enabled }),
  pullRequests: (repoId: string) => api.get<PullRequest[]>(`/repositories/${repoId}/pull-requests`),
};

// Reviews
export const reviewsApi = {
  getPrReview: (prId: string) => api.get<ReviewDetail>(`/reviews/pr/${prId}`),
  dashboard: () => api.get<DashboardStats>("/reviews/dashboard"),
  deleteReview: (prId: string) => api.delete(`/reviews/pr/${prId}`),
  rerunReview: (prId: string) => api.post(`/reviews/pr/${prId}/rerun`),
};

// Types
export interface User {
  id: string;
  name: string;
  email: string | null;
  github_username: string;
  avatar_url: string | null;
  created_at: string;
}

export interface Repository {
  id: string;
  repo_name: string;
  repo_full_name: string;
  repo_url: string;
  description: string | null;
  language: string | null;
  is_private: boolean;
  enabled: boolean;
  pr_count: number;
  created_at: string;
}

export interface PullRequest {
  id: string;
  pr_number: number;
  title: string;
  author: string;
  author_avatar: string | null;
  pr_url: string;
  status: "pending" | "processing" | "completed" | "failed";
  score: number | null;
  total_issues: number | null;
  created_at: string;
}

export interface ReviewComment {
  id: string;
  file_name: string;
  line_number: number | null;
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;
  issue: string;
  suggestion: string;
  code_snippet: string | null;
}

export interface ReviewDetail {
  review: {
    id: string;
    status: string;
    score: number;
    security_score: number | null;
    performance_score: number | null;
    quality_score: number | null;
    summary: string;
    total_issues: number;
    critical_issues: number;
    high_issues: number;
    medium_issues: number;
    low_issues: number;
    created_at: string;
  };
  pull_request: {
    id: string;
    pr_number: number;
    title: string;
    author: string;
    pr_url: string;
  };
  comments: ReviewComment[];
}

export interface DashboardStats {
  total_reviews: number;
  total_issues: number;
  repos_connected: number;
  average_score: number;
  recent_reviews: {
    pr_title: string;
    repo_name: string;
    score: number;
    total_issues: number;
    created_at: string;
    pr_id: string;
  }[];
}
