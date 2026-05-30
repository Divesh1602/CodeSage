"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reviewsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GitPullRequest, Shield, BarChart3, Star, TrendingUp, Trash2 } from "lucide-react";
import Link from "next/link";
import { getStoredUser } from "@/lib/auth";

function ScoreCircle({ score }: { score: number }) {
  const color = score >= 8 ? "text-green-600" : score >= 6 ? "text-amber-500" : "text-red-500";
  return (
    <div className={`text-3xl font-bold ${color}`}>
      {score.toFixed(1)}
      <span className="text-base text-[#9C7B72] font-normal">/10</span>
    </div>
  );
}

export default function DashboardPage() {
  const user = getStoredUser();
  const queryClient = useQueryClient();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => reviewsApi.dashboard().then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (prId: string) => reviewsApi.deleteReview(prId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-[#9C7B72]">Loading dashboard...</div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Reviews",
      value: stats?.total_reviews ?? 0,
      icon: GitPullRequest,
      color: "text-rose-500",
      bg: "bg-rose-500/10",
    },
    {
      title: "Issues Found",
      value: stats?.total_issues ?? 0,
      icon: Shield,
      color: "text-red-500",
      bg: "bg-red-500/10",
    },
    {
      title: "Repos Connected",
      value: stats?.repos_connected ?? 0,
      icon: BarChart3,
      color: "text-green-600",
      bg: "bg-green-500/10",
    },
    {
      title: "Avg Score",
      value: stats?.average_score ?? 0,
      icon: Star,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
      isScore: true,
    },
  ];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#1C0F0A]">
          Welcome back, {user?.name?.split(" ")[0] ?? "Developer"} 👋
        </h1>
        <p className="text-[#9C7B72] mt-1">Here&apos;s an overview of your code review activity.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map(({ title, value, icon: Icon, color, bg, isScore }) => (
          <Card key={title} className="bg-white border-[#F0E6E0] shadow-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`${bg} w-10 h-10 rounded-lg flex items-center justify-center`}>
                  <Icon className={`w-5 h-5 ${color}`} />
                </div>
                <TrendingUp className="w-4 h-4 text-[#D4C0B8]" />
              </div>
              {isScore ? (
                <ScoreCircle score={value as number} />
              ) : (
                <div className="text-3xl font-bold text-[#1C0F0A]">{value}</div>
              )}
              <p className="text-[#9C7B72] text-sm mt-1">{title}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Reviews */}
      <Card className="bg-white border-[#F0E6E0] shadow-sm">
        <CardHeader>
          <CardTitle className="text-[#1C0F0A] text-lg flex items-center gap-2">
            <GitPullRequest className="w-5 h-5 text-rose-500" />
            Recent Reviews
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!stats?.recent_reviews?.length ? (
            <div className="text-center py-12">
              <GitPullRequest className="w-12 h-12 text-[#E0CCC6] mx-auto mb-3" />
              <p className="text-[#9C7B72]">No reviews yet.</p>
              <p className="text-[#B8A098] text-sm mt-1">
                <Link href="/dashboard/repositories" className="text-rose-500 hover:underline">
                  Connect a repository
                </Link>{" "}
                to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {stats.recent_reviews.map((review) => (
                <div
                  key={review.pr_id}
                  className="flex items-center gap-2 bg-[#FDF3EF]/80 rounded-lg hover:bg-[#F5EDE8] transition-colors group border border-[#F0E6E0]"
                >
                  <Link
                    href={`/dashboard/reviews/${review.pr_id}`}
                    className="flex items-center justify-between flex-1 p-4 min-w-0"
                  >
                    <div className="min-w-0">
                      <p className="text-[#1C0F0A] font-medium text-sm truncate">{review.pr_title}</p>
                      <p className="text-[#9C7B72] text-xs mt-0.5">{review.repo_name}</p>
                    </div>
                    <div className="flex items-center gap-3 ml-3 flex-shrink-0">
                      <Badge variant="outline" className="text-[#9C7B72] border-[#E0CCC6] text-xs">
                        {review.total_issues} issue{review.total_issues !== 1 ? "s" : ""}
                      </Badge>
                      <div
                        className={`text-sm font-bold ${
                          review.score >= 8
                            ? "text-green-600"
                            : review.score >= 6
                            ? "text-amber-500"
                            : "text-red-500"
                        }`}
                      >
                        {review.score?.toFixed(1)}/10
                      </div>
                    </div>
                  </Link>
                  <button
                    onClick={() => deleteMutation.mutate(review.pr_id)}
                    disabled={deleteMutation.isPending}
                    className="pr-4 opacity-0 group-hover:opacity-100 transition-opacity text-[#B8A098] hover:text-red-500"
                    title="Remove review"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
