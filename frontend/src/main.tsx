import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { CreateContract } from "./pages/CreateContract";
import { ContractDetail } from "./pages/ContractDetail";
import { RaiseDispute } from "./pages/RaiseDispute";
import { DisputeDetail } from "./pages/DisputeDetail";
import { AgentCommand } from "./pages/AgentCommand";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "create", element: <CreateContract /> },
      { path: "contracts/:id", element: <ContractDetail /> },
      { path: "contracts/:id/dispute", element: <RaiseDispute /> },
      { path: "disputes/:id", element: <DisputeDetail /> },
      { path: "agent", element: <AgentCommand /> }
    ]
  }
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={new QueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>
);
