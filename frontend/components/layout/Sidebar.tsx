"use client";

import { useState } from "react";
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
  ChevronLeft,
  ChevronRight,
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
  const [collapsed, setCollapsed] = useState(false);

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-border bg-card transition-all duration-300 ease-in-out shrink-0",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Brand */}
      <div className="flex items-center justify-between px-3 py-5 min-h-[68px]">
        <Link
          href="/"
          title={collapsed ? "SmartLearnAI" : undefined}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity min-w-0"
        >
          <GraduationCap className="h-6 w-6 text-primary shrink-0" />
          <span
            className={cn(
              "text-lg font-bold tracking-tight whitespace-nowrap overflow-hidden transition-all duration-300",
              collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
            )}
          >
            SmartLearnAI
          </span>
        </Link>

        <button
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors shrink-0",
            collapsed && "mx-auto"
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      <Separator />

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map(({ label, href, icon: Icon, exact }) => {
          const isActive = exact
            ? pathname === href
            : pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                collapsed && "justify-center px-2",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span
                className={cn(
                  "whitespace-nowrap overflow-hidden transition-all duration-300",
                  collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
                )}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </nav>

      <Separator />

      {/* Bottom actions */}
      <div className="px-2 py-4 space-y-1">
        <div
          className={cn(
            "flex items-center rounded-md px-3 py-2 text-sm text-muted-foreground",
            collapsed ? "justify-center px-2" : "justify-between"
          )}
        >
          <span
            className={cn(
              "font-medium whitespace-nowrap overflow-hidden transition-all duration-300",
              collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
            )}
          >
            Theme
          </span>
          <ThemeToggle />
        </div>

        <Button
          variant="ghost"
          title={collapsed ? "Sign out" : undefined}
          className={cn(
            "w-full text-muted-foreground hover:text-destructive",
            collapsed ? "justify-center px-2" : "justify-start gap-3"
          )}
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          <span
            className={cn(
              "whitespace-nowrap overflow-hidden transition-all duration-300",
              collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
            )}
          >
            Sign out
          </span>
        </Button>
      </div>
    </aside>
  );
}
