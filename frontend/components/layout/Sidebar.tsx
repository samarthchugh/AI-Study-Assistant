"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  GraduationCap,
  LayoutDashboard,
  Upload,
  MessageSquare,
  ClipboardList,
  History,
  BarChart3,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/theme-toggle";

const navItems = [
  { label: "Dashboard",  href: "/dashboard",   icon: LayoutDashboard, exact: true  },
  { label: "Upload PDF", href: "/upload",       icon: Upload,          exact: true  },
  { label: "Ask AI",     href: "/ask",          icon: MessageSquare,   exact: true  },
  { label: "New Quiz",   href: "/quiz",         icon: ClipboardList,   exact: true  },
  { label: "My Quizzes", href: "/quiz/history", icon: History,         exact: true  },
  { label: "Analytics",  href: "/analytics",    icon: BarChart3,       exact: false },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuth();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-border bg-card">
      {/* Brand */}
      <Link href="/" className="flex items-center gap-2 px-5 py-5 hover:opacity-80 transition-opacity">
        <GraduationCap className="h-6 w-6 text-primary" />
        <span className="text-lg font-bold tracking-tight">SmartLearnAI</span>
      </Link>

      <Separator />

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ label, href, icon: Icon, exact }) => {
          const isActive = exact
            ? pathname === href
            : pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <Separator />

      {/* Bottom actions */}
      <div className="px-3 py-4 space-y-1">
        {/* Theme toggle row */}
        <div className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-muted-foreground">
          <span className="font-medium">Theme</span>
          <ThemeToggle />
        </div>

        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </Button>
      </div>
    </aside>
  );
}
