import type { ReactNode } from "react";
import { AlertCircleIcon, RotateCwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

export function EmptyState({
  icon,
  title,
  children,
  action,
}: {
  icon?: ReactNode;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-16 text-center">
      {icon && <div className="mb-4 text-muted-foreground [&_svg]:size-8 [&_svg]:stroke-[1.5]">{icon}</div>}
      <h3 className="text-base font-semibold">{title}</h3>
      {children && <div className="mt-1.5 max-w-md text-sm text-muted-foreground">{children}</div>}
      {action && <div className="mt-5 flex flex-wrap justify-center gap-2">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <EmptyState
      icon={<AlertCircleIcon />}
      title="数据加载失败"
      action={
        onRetry && (
          <Button variant="outline" onClick={onRetry}>
            <RotateCwIcon /> 重试
          </Button>
        )
      }
    >
      {message}
    </EmptyState>
  );
}

export function PageContainer({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-[1400px] px-4 py-6 sm:px-8 sm:py-8 lg:px-10 lg:py-10">{children}</div>;
}
