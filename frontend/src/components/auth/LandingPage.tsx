"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { isAuthenticated } from "@/lib/auth";
import { Github, Zap, Shield, BarChart3, GitPullRequest } from "lucide-react";

const GITHUB_CLIENT_ID = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "";

export function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.push("/dashboard");
    }
  }, [router]);

  const handleGitHubLogin = () => {
    const redirectUri = `${window.location.origin}/auth/callback`;
    const url = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&scope=repo,read:user,user:email&redirect_uri=${redirectUri}`;
    window.location.assign(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FDF8F6] via-rose-50 to-[#FFF0EC]">
      {/* Nav */}
      <nav className="border-b border-[#E8D8D0] px-6 py-4 flex items-center justify-between bg-white/70 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-rose-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-[#1C0F0A] font-bold text-xl">CodeSage</span>
        </div>
        <Button
          onClick={handleGitHubLogin}
          className="bg-[#1C0F0A] text-white hover:bg-[#3D2018] gap-2"
        >
          <Github className="w-4 h-4" />
          Sign in with GitHub
        </Button>
      </nav>

      {/* Hero */}
      <div className="max-w-5xl mx-auto px-6 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-rose-500/10 border border-rose-500/20 rounded-full px-4 py-1.5 text-rose-600 text-sm mb-8">
          <Zap className="w-3.5 h-3.5" />
          AI-Powered Code Reviews
        </div>

        <h1 className="text-5xl md:text-7xl font-bold text-[#1C0F0A] mb-6 leading-tight">
          Review code smarter
          <br />
          <span className="text-rose-500">with AI agents</span>
        </h1>

        <p className="text-xl text-[#9C7B72] max-w-2xl mx-auto mb-10">
          Connect your GitHub repositories. CodeSage automatically reviews every pull request using
          specialized AI agents for security, performance, quality, and testing.
        </p>

        <Button
          onClick={handleGitHubLogin}
          size="lg"
          className="bg-rose-600 hover:bg-rose-700 text-white gap-2 text-lg px-8 h-14"
        >
          <Github className="w-5 h-5" />
          Continue with GitHub
        </Button>

        <p className="text-[#B8A098] text-sm mt-4">Free to use. No credit card required.</p>
      </div>

      {/* Features */}
      <div className="max-w-5xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              icon: Shield,
              title: "Security Analysis",
              desc: "Detect SQL injection, exposed secrets, auth flaws, and more",
              color: "text-red-500",
              bg: "bg-red-50",
            },
            {
              icon: Zap,
              title: "Performance Issues",
              desc: "Spot N+1 queries, inefficient loops, and memory leaks",
              color: "text-amber-500",
              bg: "bg-amber-50",
            },
            {
              icon: BarChart3,
              title: "Code Quality",
              desc: "Enforce SOLID principles, naming conventions, and complexity limits",
              color: "text-green-600",
              bg: "bg-green-50",
            },
            {
              icon: GitPullRequest,
              title: "Test Coverage",
              desc: "Get AI-generated test cases for uncovered edge cases",
              color: "text-rose-500",
              bg: "bg-rose-50",
            },
          ].map(({ icon: Icon, title, desc, color, bg }) => (
            <div
              key={title}
              className="bg-white border border-[#F0E6E0] rounded-xl p-6 hover:border-[#E8D8D0] hover:shadow-md transition-all"
            >
              <div className={`${bg} w-10 h-10 rounded-lg flex items-center justify-center mb-4`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <h3 className="text-[#1C0F0A] font-semibold mb-2">{title}</h3>
              <p className="text-[#9C7B72] text-sm">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
