"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, GitBranch, GitPullRequest, LogOut, Zap } from "lucide-react";
import { removeToken } from "@/lib/auth";
import { useRouter } from "next/navigation";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/dashboard/repositories", icon: GitBranch, label: "Repositories" },
  { href: "/dashboard/reviews", icon: GitPullRequest, label: "Reviews" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    removeToken();
    router.push("/");
  };

  return (
    <aside className="w-64 bg-[#F5EDE8] border-r border-[#E8D8D0] flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-[#E8D8D0]">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-rose-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-[#1C0F0A] font-bold text-lg">CodeSage</span>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname === href
                ? "bg-rose-500/15 text-rose-600"
                : "text-[#9C7B72] hover:text-[#1C0F0A] hover:bg-[#EDD8D0]"
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#E8D8D0]">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-[#9C7B72] hover:text-[#1C0F0A] hover:bg-[#EDD8D0] w-full transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
