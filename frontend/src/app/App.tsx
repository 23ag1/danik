import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "../shared/ui/Layout";
import { DashboardPage } from "../pages/DashboardPage";
import { IncidentsPage } from "../pages/IncidentsPage";
import { IncidentDetailPage } from "../pages/IncidentDetailPage";
import { IngestPage } from "../pages/IngestPage";
import { EventsPage } from "../pages/EventsPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="incidents/:id" element={<IncidentDetailPage />} />
          <Route path="ingest" element={<IngestPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
