import { createBrowserRouter } from "react-router";

import { AppShell } from "@/components/layout/AppShell";
import { AttributeIndexPage } from "@/pages/AttributeIndexPage";
import { CharacterPage } from "@/pages/CharacterPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { SearchPage } from "@/pages/SearchPage";
import { WorkPage } from "@/pages/WorkPage";
import { WorksPage } from "@/pages/WorksPage";

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { index: true, element: <SearchPage /> },
      { path: "characters/:id", element: <CharacterPage /> },
      { path: "works", element: <WorksPage /> },
      { path: "works/:id", element: <WorkPage /> },
      { path: "attributes", element: <AttributeIndexPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
