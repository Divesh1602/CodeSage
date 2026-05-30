"use client";

import { useQuery } from "@tanstack/react-query";
import { reposApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { GitPullRequest, Clock, CheckCircle, XCircle, Loader } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Repository } from "@/lib/api";
import { reposApi as reposApiImport } from "@/lib/api";

const statusIcon = {
  pending: <Clock className="w-4 h-4 text-amber-500" />,
  processing: <Loader className="w-4 h-4 text-rose-500 animate-spin" />,
  completed: <CheckCircle className="w-4 h-4 text-green-600" />,
  failed: <XCircle className="w-4 h-4 text-red-500" />,
};

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-[#B8A098] text-sm">—</span>;
  const color = score >= 8 ? "text-green-600" : score >= 6 ? "text-amber-500" : "text-red-500";
  return <span className={`font-bold text-sm ${color}`}>{score.toFixed(1)}/10</span>;
}

export default function ReviewsPage() {
  const [repos, setRepos] = useState<Repository[]>([]);

  useEffect(() => {
    reposApiImport.list().then((r) => setRepos(r.data));
  }, []);

  const enabledRepos = repos.filter((r) => r.enabled);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#1C0F0A]">Pull Request Reviews</h1>
        <p className="text-[#9C7B72] mt-1">AI-generated reviews for your pull requests.</p>
      </div>

      {!enabledRepos.length ? (
        <Card className="bg-white border-[#F0E6E0] shadow-sm">
          <CardContent className="py-16 text-center">
            <GitPullRequest className="w-12 h-12 text-[#E0CCC6] mx-auto mb-3" />
            <p className="text-[#9C7B72]">No enabled repositories.</p>
            <p className="text-[#B8A098] text-sm mt-1">
              <Link href="/dashboard/repositories" className="text-rose-500 hover:underline">
                Enable a repository
              </Link>{" "}
              to start receiving reviews.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
          {enabledRepos.map((repo) => (
            <RepoPRList key={repo.id} repo={repo} />
          ))}
        </div>
      )}
    </div>
  );
}

function RepoPRList({ repo }: { repo: Repository }) {
  const { data: prs, isLoading } = useQuery({
    queryKey: ["prs", repo.id],
    queryFn: () => reposApi.pullRequests(repo.id).then((r) => r.data),
    refetchInterval: 30000,
  });

  return (
    <div>
      <h2 className="text-[#3D2018] font-semibold mb-3 flex items-center gap-2">
        <GitPullRequest className="w-4 h-4 text-rose-500" />
        {repo.repo_full_name}
      </h2>

      {isLoading ? (
        <div className="text-[#B8A098] text-sm">Loading...</div>
      ) : !prs?.length ? (
        <div className="text-[#B8A098] text-sm pl-6">No pull requests found.</div>
      ) : (
        <Card className="bg-white border-[#F0E6E0] shadow-sm">
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#F0E6E0]">
                  <th className="text-left px-4 py-3 text-[#9C7B72] text-xs font-medium">PR</th>
                  <th className="text-left px-4 py-3 text-[#9C7B72] text-xs font-medium">Author</th>
                  <th className="text-left px-4 py-3 text-[#9C7B72] text-xs font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-[#9C7B72] text-xs font-medium">Score</th>
                  <th className="text-left px-4 py-3 text-[#9C7B72] text-xs font-medium">Issues</th>
                  <th className="text-left px-4 py-3 text-[#9C7B72] text-xs font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {prs.map((pr, i) => (
                  <tr
                    key={pr.id}
                    className={`${i < prs.length - 1 ? "border-b border-[#F0E6E0]" : ""} hover:bg-[#F5EDE8] transition-colors`}
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/reviews/${pr.id}`}
                        className="text-[#1C0F0A] hover:text-rose-600 font-medium text-sm line-clamp-1 transition-colors"
                      >
                        #{pr.pr_number} {pr.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-[#9C7B72] text-sm">{pr.author}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {statusIcon[pr.status]}
                        <span className="text-xs text-[#9C7B72] capitalize">{pr.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={pr.score} />
                    </td>
                    <td className="px-4 py-3 text-[#9C7B72] text-sm">
                      {pr.total_issues ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-[#B8A098] text-xs">
                      {new Date(pr.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
