"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reviewsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Shield,
  Zap,
  Star,
  TestTube,
  AlertTriangle,
  Info,
  ExternalLink,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

const severityConfig = {
  critical: { label: "Critical", color: "text-red-500", bg: "bg-red-50 border-red-200", badge: "critical" as const },
  high: { label: "High", color: "text-orange-500", bg: "bg-orange-50 border-orange-200", badge: "high" as const },
  medium: { label: "Medium", color: "text-amber-500", bg: "bg-amber-50 border-amber-200", badge: "medium" as const },
  low: { label: "Low", color: "text-green-600", bg: "bg-green-50 border-green-200", badge: "low" as const },
  info: { label: "Info", color: "text-blue-500", bg: "bg-blue-50 border-blue-200", badge: "info" as const },
};

const categoryConfig = {
  security: { icon: Shield, label: "Security", color: "text-red-500" },
  performance: { icon: Zap, label: "Performance", color: "text-amber-500" },
  quality: { icon: Star, label: "Quality", color: "text-green-600" },
  testing: { icon: TestTube, label: "Testing", color: "text-rose-500" },
};

function ScoreGauge({ score, label }: { score: number | null; label: string }) {
  if (score === null) return null;
  const color = score >= 8 ? "text-green-600" : score >= 6 ? "text-amber-500" : "text-red-500";
  const barColor = score >= 8 ? "bg-green-500" : score >= 6 ? "bg-amber-400" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-[#9C7B72] text-xs">{label}</span>
        <span className={`${color} text-xs font-bold`}>{score.toFixed(1)}/10</span>
      </div>
      <div className="h-1.5 bg-[#F0E6E0] rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${score * 10}%` }} />
      </div>
    </div>
  );
}

export default function ReviewDetailPage({ params }: { params: { prId: string } }) {
  const { prId } = params;
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["review", prId],
    queryFn: () => reviewsApi.getPrReview(prId).then((r) => r.data),
  });

  const rerunMutation = useMutation({
    mutationFn: () => reviewsApi.rerunReview(prId),
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["review", prId] }), 3000);
    },
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-[#9C7B72]">Loading review...</div>
      </div>
    );
  }

  if (error || !data) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const httpStatus = (error as any)?.response?.status;
    const isNotFound = httpStatus === 404;
    return (
      <div className="p-8 max-w-5xl">
        <Link
          href="/dashboard/reviews"
          className="flex items-center gap-2 text-[#9C7B72] hover:text-[#1C0F0A] text-sm mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Reviews
        </Link>
        <Card className="bg-white border-[#F0E6E0] shadow-sm">
          <CardContent className="py-16 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-[#1C0F0A] font-medium text-lg mb-2">
              {isNotFound ? "Review not found" : "Failed to load review"}
            </p>
            <p className="text-[#9C7B72] text-sm mb-6">
              {isNotFound
                ? "This PR hasn't been reviewed yet or the review was deleted."
                : "Something went wrong loading this review."}
            </p>
            {isNotFound && (
              <button
                onClick={() => rerunMutation.mutate()}
                disabled={rerunMutation.isPending || rerunMutation.isSuccess}
                className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-60 text-white rounded-lg text-sm transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${rerunMutation.isPending ? "animate-spin" : ""}`} />
                {rerunMutation.isSuccess ? "Queued — check back soon" : "Run Analysis"}
              </button>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  const { review, pull_request: pr, comments } = data;
  const overallScore = review.score ?? 0;
  const scoreColor = overallScore >= 8 ? "text-green-600" : overallScore >= 6 ? "text-amber-500" : "text-red-500";
  const analysisIncomplete =
    review.status === "failed" ||
    (review.security_score === null && review.performance_score === null && review.quality_score === null);

  const commentsByCategory: Record<string, typeof comments> = {};
  for (const c of comments) {
    const cat = c.category ?? "general";
    commentsByCategory[cat] = [...(commentsByCategory[cat] ?? []), c];
  }

  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/dashboard/reviews"
          className="flex items-center gap-2 text-[#9C7B72] hover:text-[#1C0F0A] text-sm mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Reviews
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#1C0F0A]">
              #{pr.pr_number} {pr.title}
            </h1>
            <div className="flex items-center gap-3 mt-2">
              <span className="text-[#9C7B72] text-sm">by @{pr.author}</span>
              {pr.pr_url && (
                <a
                  href={pr.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-rose-500 hover:text-rose-600 text-sm flex items-center gap-1 transition-colors"
                >
                  View on GitHub <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className={`text-4xl font-bold ${scoreColor}`}>
              {overallScore.toFixed(1)}
              <span className="text-lg text-[#9C7B72] font-normal">/10</span>
            </div>
            <p className="text-[#9C7B72] text-sm">Overall Score</p>
          </div>
        </div>
      </div>

      {/* Incomplete analysis banner */}
      {analysisIncomplete && (
        <div className="flex items-center justify-between gap-4 mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
            <div>
              <p className="text-amber-700 text-sm font-medium">Analysis incomplete</p>
              <p className="text-amber-600/80 text-xs mt-0.5">
                The AI agents couldn&apos;t process this PR. Re-run the analysis to get results.
              </p>
            </div>
          </div>
          <button
            onClick={() => rerunMutation.mutate()}
            disabled={rerunMutation.isPending || rerunMutation.isSuccess}
            className="flex-shrink-0 inline-flex items-center gap-2 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-white rounded-lg text-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${rerunMutation.isPending ? "animate-spin" : ""}`} />
            {rerunMutation.isSuccess ? "Queued!" : "Re-run Analysis"}
          </button>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
        {[
          { label: "Total", value: review.total_issues, color: "text-[#1C0F0A]" },
          { label: "Critical", value: review.critical_issues, color: "text-red-500" },
          { label: "High", value: review.high_issues, color: "text-orange-500" },
          { label: "Medium", value: review.medium_issues, color: "text-amber-500" },
          { label: "Low", value: review.low_issues, color: "text-green-600" },
        ].map(({ label, value, color }) => (
          <Card key={label} className="bg-white border-[#F0E6E0] shadow-sm">
            <CardContent className="p-4 text-center">
              <div className={`text-2xl font-bold ${color}`}>{value}</div>
              <p className="text-[#9C7B72] text-xs mt-0.5">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Scores */}
      <Card className="bg-white border-[#F0E6E0] shadow-sm mb-6">
        <CardHeader>
          <CardTitle className="text-[#1C0F0A] text-base">Score Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ScoreGauge score={review.security_score} label="Security" />
          <ScoreGauge score={review.performance_score} label="Performance" />
          <ScoreGauge score={review.quality_score} label="Code Quality" />
        </CardContent>
      </Card>

      {/* Summary */}
      {review.summary && (
        <Card className="bg-white border-[#F0E6E0] shadow-sm mb-6">
          <CardContent className="p-5">
            <div className="flex gap-3">
              <Info className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
              <p className="text-[#3D2018] text-sm leading-relaxed">{review.summary}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Issues by Category */}
      {Object.entries(commentsByCategory).map(([category, issues]) => {
        const config = categoryConfig[category as keyof typeof categoryConfig];
        const Icon = config?.icon ?? AlertTriangle;
        return (
          <div key={category} className="mb-6">
            <h2 className="text-[#1C0F0A] font-semibold mb-3 flex items-center gap-2">
              <Icon className={`w-4 h-4 ${config?.color ?? "text-[#9C7B72]"}`} />
              {config?.label ?? category} Issues
              <span className="text-[#B8A098] text-sm font-normal">({issues.length})</span>
            </h2>
            <div className="space-y-3">
              {issues.map((comment) => {
                const sev = comment.severity as keyof typeof severityConfig;
                const sevConfig = severityConfig[sev] ?? severityConfig.info;
                return (
                  <Card
                    key={comment.id}
                    className={`bg-white border ${sevConfig.bg}`}
                  >
                    <CardContent className="p-5">
                      <div className="flex items-start gap-3">
                        <Badge variant={sevConfig.badge} className="mt-0.5 flex-shrink-0">
                          {sevConfig.label}
                        </Badge>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[#3D2018] text-xs font-mono bg-[#F5EDE8] px-2 py-0.5 rounded">
                              {comment.file_name}
                              {comment.line_number ? `:${comment.line_number}` : ""}
                            </span>
                          </div>
                          <p className="text-[#1C0F0A] text-sm mb-2">{comment.issue}</p>
                          {comment.suggestion && (
                            <div className="bg-[#F5EDE8]/60 border border-[#E8D8D0] rounded-md p-3">
                              <p className="text-xs text-[#9C7B72] mb-1 font-medium">Suggestion</p>
                              <p className="text-[#3D2018] text-sm">{comment.suggestion}</p>
                            </div>
                          )}
                          {comment.code_snippet && (
                            <pre className="mt-2 bg-[#F5EDE8] rounded-md p-3 text-xs text-[#3D2018] overflow-x-auto">
                              <code>{comment.code_snippet}</code>
                            </pre>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        );
      })}

      {comments.length === 0 && (
        <Card className="bg-white border-[#F0E6E0] shadow-sm">
          <CardContent className="py-12 text-center">
            <Star className="w-10 h-10 text-green-500 mx-auto mb-3" />
            <p className="text-[#1C0F0A] font-medium">No issues found!</p>
            <p className="text-[#9C7B72] text-sm mt-1">This PR looks clean.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
