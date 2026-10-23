import { Link } from "react-router";
import { CompassIcon } from "lucide-react";

import { EmptyState, PageContainer } from "@/components/States";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <PageContainer>
      <EmptyState
        icon={<CompassIcon />}
        title="页面不存在"
        action={
          <Button asChild variant="outline">
            <Link to="/">回到角色检索</Link>
          </Button>
        }
      />
    </PageContainer>
  );
}
