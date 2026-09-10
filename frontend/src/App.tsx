import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { AdminPage } from "./pages/AdminPage";
import { LoginPage } from "./pages/LoginPage";
import { MarketDetailPage } from "./pages/MarketDetailPage";
import { MarketsListPage } from "./pages/MarketsListPage";
import { MeetDetailPage } from "./pages/MeetDetailPage";
import { MeetsListPage } from "./pages/MeetsListPage";
import { PortfolioPage } from "./pages/PortfolioPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SignupPage } from "./pages/SignupPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/markets" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/markets" element={<MarketsListPage />} />
        <Route path="/markets/:marketId" element={<MarketDetailPage />} />
        <Route path="/meets" element={<MeetsListPage />} />
        <Route path="/meets/:meetId" element={<MeetDetailPage />} />
        <Route
          path="/portfolio"
          element={
            <RequireAuth>
              <PortfolioPage />
            </RequireAuth>
          }
        />
        <Route
          path="/settings"
          element={
            <RequireAuth>
              <SettingsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireAuth adminOnly>
              <AdminPage />
            </RequireAuth>
          }
        />
      </Route>
    </Routes>
  );
}
