"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { authApi } from "@/lib/api";
import { setToken, setStoredUser } from "@/lib/auth";
import { Zap } from "lucide-react";

function CallbackHandler() {
  const router = useRouter();
  const params = useSearchParams();
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    const code = params.get("code");
    if (!code) {
      router.replace("/");
      return;
    }
    called.current = true;

    authApi
      .githubCallback(code)
      .then(({ data }) => {
        setToken(data.access_token);
        setStoredUser(data.user);
        router.replace("/dashboard");
      })
      .catch(() => router.replace("/?error=auth_failed"));
  }, [params, router]);

  return (
    <div className="min-h-screen bg-[#FDF8F6] flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 bg-rose-600 rounded-xl flex items-center justify-center mx-auto mb-4 animate-pulse">
          <Zap className="w-7 h-7 text-white" />
        </div>
        <p className="text-[#1C0F0A] text-lg font-medium">Signing you in...</p>
        <p className="text-[#9C7B72] text-sm mt-1">Connecting to GitHub</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense>
      <CallbackHandler />
    </Suspense>
  );
}
