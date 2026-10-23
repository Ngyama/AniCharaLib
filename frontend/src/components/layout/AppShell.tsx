import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router";
import { MenuIcon } from "lucide-react";
import { Dialog as DialogPrimitive } from "radix-ui";

import { Button } from "@/components/ui/button";
import { Brand, SidebarNav } from "./Sidebar";

/**
 * Floating panel layout: navigation sits directly on the shell background, the page
 * content lives in an inset rounded panel that scrolls on its own.
 */
export function AppShell() {
  const panelRef = useRef<HTMLElement>(null);
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    panelRef.current?.scrollTo({ top: 0 });
    setMenuOpen(false);
  }, [pathname]);

  return (
    <div className="flex h-dvh flex-col lg:flex-row lg:gap-3 lg:p-3">
      <aside className="hidden w-60 shrink-0 lg:flex lg:flex-col">
        <SidebarNav />
      </aside>

      {/* Mobile top bar */}
      <header className="flex items-center justify-between px-4 pt-3 pb-2 lg:hidden">
        <Brand />
        <DialogPrimitive.Root open={menuOpen} onOpenChange={setMenuOpen}>
          <DialogPrimitive.Trigger asChild>
            <Button variant="ghost" size="icon" aria-label="打开导航">
              <MenuIcon />
            </Button>
          </DialogPrimitive.Trigger>
          <DialogPrimitive.Portal>
            <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-overlay data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0" />
            <DialogPrimitive.Content className="fixed inset-y-2 left-2 z-50 flex w-72 flex-col rounded-2xl bg-shell p-3 shadow-xl outline-none data-[state=open]:animate-in data-[state=open]:slide-in-from-left-4 data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left-4">
              <DialogPrimitive.Title className="sr-only">导航</DialogPrimitive.Title>
              <DialogPrimitive.Description className="sr-only">站点导航</DialogPrimitive.Description>
              <SidebarNav />
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        </DialogPrimitive.Root>
      </header>

      <main
        ref={panelRef}
        className="relative mx-2 mb-2 flex-1 overflow-y-auto rounded-2xl border border-border/70 bg-panel shadow-[0_1px_2px_oklch(0.2_0.01_300/0.04),0_8px_24px_-12px_oklch(0.2_0.01_300/0.08)] scrollbar-thin lg:m-0 lg:rounded-3xl"
      >
        <Outlet />
      </main>
    </div>
  );
}
