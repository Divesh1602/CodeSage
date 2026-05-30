"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reposApi, Repository } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  GitPullRequest,
  RefreshCw,
  Lock,
  Globe,
  GitBranch,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3B82F6",
  JavaScript: "#F59E0B",
  Python: "#22C55E",
  Go: "#06B6D4",
  Rust: "#F97316",
  Java: "#EF4444",
  "C++": "#EC4899",
  CSS: "#A78BFA",
  HTML: "#F97316",
};

function LanguageDot({ lang }: { lang: string | null }) {
  if (!lang) return null;
  const color = LANG_COLORS[lang] ?? "#94A3B8";
  return (
    <span className="flex items-center gap-1.5 text-[#9C7B72] text-xs">
      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      {lang}
    </span>
  );
}

function ToggleSwitch({
  enabled,
  loading,
  onToggle,
}: {
  enabled: boolean;
  loading: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      disabled={loading}
      aria-checked={enabled}
      role="switch"
      className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-rose-400 focus:ring-offset-2 focus:ring-offset-white disabled:cursor-not-allowed disabled:opacity-60 ${
        enabled ? "bg-rose-600" : "bg-[#D4C0B8]"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200 ${
          enabled ? "translate-x-6" : "translate-x-1"
        } ${loading ? "animate-pulse" : ""}`}
      />
    </button>
  );
}

function RepoCard({
  repo,
  toggling,
  onToggle,
}: {
  repo: Repository;
  toggling: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className={`relative flex items-center gap-4 rounded-xl border px-5 py-4 transition-all duration-150 ${
        repo.enabled
          ? "border-rose-200 bg-rose-50/60"
          : "border-[#F0E6E0] bg-white hover:border-[#E0CCC4] hover:bg-[#FDFAF9]"
      }`}
    >
      {/* Left accent */}
      {repo.enabled && (
        <div className="absolute left-0 top-4 bottom-4 w-[3px] rounded-full bg-rose-500" />
      )}

      {/* Repo info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
          {/* Use span + onClick to avoid visited-link color pollution */}
          <a
            href={repo.repo_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "inherit", textDecoration: "none" }}
            className="text-sm font-semibold text-[#1C0F0A] hover:text-rose-600 transition-colors flex items-center gap-1.5 min-w-0 visited:text-[#1C0F0A]"
          >
            <span className="truncate">{repo.repo_full_name}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0 text-[#B8A098]" />
          </a>
          {repo.is_private ? (
            <span className="flex items-center gap-1 text-xs text-[#B8A098] flex-shrink-0">
              <Lock className="w-3 h-3" /> Private
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-[#B8A098] flex-shrink-0">
              <Globe className="w-3 h-3" /> Public
            </span>
          )}
        </div>

        {repo.description && (
          <p className="text-[#B8A098] text-xs mb-2 line-clamp-1">{repo.description}</p>
        )}

        <div className="flex items-center gap-4">
          <LanguageDot lang={repo.language} />
          <span className="flex items-center gap-1 text-[#B8A098] text-xs">
            <GitPullRequest className="w-3 h-3" />
            {repo.pr_count ?? 0} PRs
          </span>
        </div>
      </div>

      {/* Right: status + toggle — fixed width prevents layout shift */}
      <div className="flex items-center gap-3 flex-shrink-0 w-32 justify-end">
        <span
          className={`text-xs font-medium w-14 text-right ${
            repo.enabled ? "text-rose-600" : "text-[#B8A098]"
          }`}
        >
          {repo.enabled ? "Enabled" : "Disabled"}
        </span>
        <ToggleSwitch enabled={repo.enabled} loading={toggling} onToggle={onToggle} />
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-[#B8A098] mb-3 px-1">
      {children}
    </p>
  );
}

export default function RepositoriesPage() {
  const qc = useQueryClient();
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const { data: repos, isLoading } = useQuery({
    queryKey: ["repositories"],
    queryFn: () => reposApi.list().then((r) => r.data),
  });

  const syncMutation = useMutation({
    mutationFn: () => reposApi.sync().then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["repositories"] }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      reposApi.toggle(id, enabled).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["repositories"] });
      setTogglingId(null);
    },
    onError: () => setTogglingId(null),
  });

  const handleToggle = (repo: Repository) => {
    setTogglingId(repo.id);
    toggleMutation.mutate({ id: repo.id, enabled: !repo.enabled });
  };

  const enabledRepos = repos?.filter((r) => r.enabled) ?? [];
  const disabledRepos = repos?.filter((r) => !r.enabled) ?? [];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1C0F0A]">Repositories</h1>
          <p className="text-[#9C7B72] text-sm mt-1">
            Enable AI code review for your GitHub repositories.
          </p>
          {repos && repos.length > 0 && (
            <div className="flex items-center gap-1.5 mt-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-rose-500" />
              <p className="text-[#9C7B72] text-xs">
                <span className="text-rose-600 font-semibold">{enabledRepos.length}</span> of {repos.length} repos active
              </p>
            </div>
          )}
        </div>
        <Button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          variant="outline"
          size="sm"
          className="border-[#E8D8D0] text-[#3D2018] hover:bg-[#EDD8D0] hover:text-[#1C0F0A] gap-2 mt-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`} />
          Sync from GitHub
        </Button>
      </div>

      {/* Body */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-[68px] rounded-xl bg-[#F5EDE8] border border-[#F0E6E0] animate-pulse" />
          ))}
        </div>
      ) : !repos?.length ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#F0E6E0] flex items-center justify-center mb-4">
            <GitBranch className="w-7 h-7 text-[#C8B0A8]" />
          </div>
          <p className="text-[#3D2018] font-medium mb-1">No repositories found</p>
          <p className="text-[#9C7B72] text-sm mb-6">Sync your GitHub account to get started.</p>
          <Button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="bg-rose-600 hover:bg-rose-700 text-white gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
            Sync Repositories
          </Button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Enabled section */}
          {enabledRepos.length > 0 && (
            <div>
              <SectionLabel>Active — AI review on</SectionLabel>
              <div className="space-y-2">
                {enabledRepos.map((repo) => (
                  <RepoCard
                    key={repo.id}
                    repo={repo}
                    toggling={togglingId === repo.id}
                    onToggle={() => handleToggle(repo)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Disabled section */}
          {disabledRepos.length > 0 && (
            <div>
              <SectionLabel>
                {enabledRepos.length > 0 ? "Available repositories" : "All repositories"}
              </SectionLabel>
              <div className="space-y-2">
                {disabledRepos.map((repo) => (
                  <RepoCard
                    key={repo.id}
                    repo={repo}
                    toggling={togglingId === repo.id}
                    onToggle={() => handleToggle(repo)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
