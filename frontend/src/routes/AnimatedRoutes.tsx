import { AnimatePresence } from "framer-motion";
import { AuthProvider } from "@/context/AuthContext.tsx";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import NotFound from "@/pages/NotFound.tsx";
import { Login } from "@/pages/Authentication/Login.tsx";
import Authentication from "@/pages/Authentication";
import Layout from "@/components/layout/Layout";
import { Path } from "@/lib/types";
import HomePage from "@/pages/HomePage.tsx";
import { PrivateRoute } from "@/routes/PrivateRoute.tsx";
import TopicPage from "@/pages/TopicPage.tsx";
import TopicDetailsPage from "@/pages/TopicDetailsPage.tsx";
import KnowledgeBase from "@/pages/KnowledgeBase.tsx";
import ContentDeskPage from "@/pages/ContentDesk.tsx";
import SettingsPage from "@/pages/SettingsPage.tsx";
import PendingPosts from "@/components/pending_posts/PendingPosts.tsx";

export const AnimatedRoutes = () => {
  return (
    <AnimatePresence>
      <AuthProvider>
        <Routes location={useLocation()}>
          <Route key={Path.AUTH} path={Path.AUTH} element={<Authentication />}>
            <Route path={Path.LOGIN} element={<Login />} />
          </Route>
          <Route
            key={Path.HOME}
            path={Path.HOME}
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route key={Path.HOME} index element={<HomePage />} />
            <Route key={Path.TOPIC} path={Path.TOPIC} element={<TopicPage />} />
            <Route
              key={`${Path.TOPIC}_DETAILS`}
              path={`${Path.TOPIC}/:id`}
              element={<TopicDetailsPage />}
            >
              <Route index element={<Navigate to="desks" replace />} />
              <Route
                key={Path.KNOWLEDGE_BASE}
                path={Path.KNOWLEDGE_BASE}
                element={<KnowledgeBase />}
              />
              <Route
                key={Path.CONTENTDESK}
                path={Path.CONTENTDESK}
                element={<ContentDeskPage />}
              />
              <Route
                key={Path.PENDING_POSTS}
                path={Path.PENDING_POSTS}
                element={<PendingPosts />}
              />
              <Route
                key={Path.SETTINGS}
                path={Path.SETTINGS}
                element={<SettingsPage />}
              />
            </Route>
            <Route
              key={Path.SETTINGS}
              path={Path.SETTINGS}
              element={<SettingsPage />}
            />
          </Route>
          <Route key="*" path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </AnimatePresence>
  );
};
