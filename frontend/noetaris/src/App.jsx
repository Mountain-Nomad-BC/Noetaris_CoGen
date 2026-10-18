import "@/App.css";
import React, { Suspense, lazy } from "react";
import LiveAuthGate from "@/noetaris/components/LiveAuthGate";
import { AuthProvider } from "@/noetaris/state/AuthContext";
import PageErrorBoundary from "@/noetaris/components/PageErrorBoundary";
import { VoiceProvider } from "@/noetaris/state/VoiceContext";
import { ConversationProvider } from "@/noetaris/state/ConversationContext";
import { UserPrefsProvider } from "@/noetaris/state/UserPrefsContext";
import { LiveQueueProvider } from '@/noetaris/state/LiveQueueContext';
import { LiveGovernedProvider } from '@/noetaris/state/LiveGovernedContext';
import { LiveClaimReviewProvider } from '@/noetaris/state/LiveClaimReviewContext';
import { LiveLearningProvider } from '@/noetaris/state/LiveLearningContext';
import { LiveChatProvider } from '@/noetaris/state/LiveChatContext';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import AppShell from "@/noetaris/layout/AppShell";
import { mode } from "@/noetaris/services/api";

function PreviewOnlyFeature({ name, children }) {
  if (mode !== "live") return children;
  return (
    <section className="p-4 md:p-8" role="status" data-testid="live-feature-unavailable">
      <div className="n-glass max-w-2xl rounded-2xl p-6">
        <p className="n-chip n-chip-amber inline-block mb-4">NOT AVAILABLE IN LIVE MODE</p>
        <h1 className="font-display text-2xl mb-3">{name}</h1>
        <p className="text-sm text-[color:var(--n-text-mute)]">
          This screen has no qualified live operation. Preview fixtures and sample actions are withheld.
        </p>
      </div>
    </section>
  );
}

// Public Marketing & Auth Pages
const LandingPage = lazy(() => import("@/noetaris/pages/public/LandingPage"));
const LoginPage = lazy(() => import("@/noetaris/pages/public/LoginPage"));
const PlatformPage = lazy(() => import("@/noetaris/pages/public/MarketingPages").then(m => ({ default: m.PlatformPage })));
const CapabilitiesPage = lazy(() => import("@/noetaris/pages/public/MarketingPages").then(m => ({ default: m.CapabilitiesPage })));
const ArchitecturePage = lazy(() => import("@/noetaris/pages/public/MarketingPages").then(m => ({ default: m.ArchitecturePage })));
const DevelopersPage = lazy(() => import("@/noetaris/pages/public/MarketingPages").then(m => ({ default: m.DevelopersPage })));
const DocsPage = lazy(() => import("@/noetaris/pages/public/ProjectDocumentPage"));
const ProjectDocumentPage = DocsPage;
const ContactPage = lazy(() => import("@/noetaris/pages/public/MarketingPages").then(m => ({ default: m.ContactPage })));

// Core Live Application Pages
const CommandCenter = lazy(() => import("@/noetaris/pages/app/CommandCenter"));
const LibraryPage = lazy(() => import("@/noetaris/pages/app/LiveLibrary"));
const PdfWorkspace = lazy(() => import("@/noetaris/pages/app/LivePdfWorkspace"));
const ChatPage = lazy(() => import("@/noetaris/pages/app/LiveChatPage"));
const KnowledgeExplorer = lazy(() => import("@/noetaris/pages/app/LiveKnowledgeExplorer"));
const LiveClaimReviewPage = lazy(() => import("@/noetaris/pages/app/LiveClaimReviewPage"));
const LiveGovernedPage = lazy(() => import("@/noetaris/pages/app/LiveGovernedPage"));
const LiveLearningPage = lazy(() => import("@/noetaris/pages/app/LiveLearningPage"));
const LiveMemoryPage = lazy(() => import("@/noetaris/pages/app/LiveMemoryPage"));
const LiveQueuePage = lazy(() => import("@/noetaris/pages/app/LiveQueuePage"));
const ResearchPage = lazy(() => import("@/noetaris/pages/app/ResearchPage"));
const AnalyticsPage = lazy(() => import("@/noetaris/pages/app/AnalyticsPage"));
const IntegrationsPage = lazy(() => import("@/noetaris/pages/app/IntegrationsPage"));
const TemplatesPage = lazy(() => import("@/noetaris/pages/app/TemplatesPage"));
const AgentsPage = lazy(() => import("@/noetaris/pages/app/AgentsPage"));
const EvaluationsPage = lazy(() => import("@/noetaris/pages/app/EvaluationsPage"));
const WorkflowStudio = lazy(() => import("@/noetaris/pages/app/WorkflowStudio"));
const ContractsPage = lazy(() => import("@/noetaris/pages/app/ContractsPage"));
const ExecutionsPage = lazy(() => import("@/noetaris/pages/app/ExecutionsPage"));
const DemoControlsPage = lazy(() => import("@/noetaris/pages/app/DemoControlsPage"));

// Operational Management Pages
const operations = () => import("@/noetaris/pages/app/OperationsPages");
const LiveOperationsPage = lazy(() => import("@/noetaris/pages/app/LiveOperationsPage"));
const CostsPage = lazy(() => import("@/noetaris/pages/app/LiveCostsPage"));
const AuditPage = lazy(() => operations().then(m => ({ default: m.AuditPage })));
const GovernancePage = lazy(() => operations().then(m => ({ default: m.GovernancePage })));
const SettingsPage = lazy(() => operations().then(m => ({ default: m.SettingsPage })));
const NotificationsPage = lazy(() => operations().then(m => ({ default: m.NotificationsPage })));
const ModelsPage = lazy(() => operations().then(m => ({ default: m.ModelsPage })));
const ObservabilityPage = lazy(() => operations().then(m => ({ default: m.ObservabilityPage })));
const WorkflowsPage = lazy(() => operations().then(m => ({ default: m.WorkflowsPage })));

function RootPage() {
  const location = useLocation();
  const result = new URLSearchParams(location.search).get('auth');
  if (['complete', 'failed', 'cancelled'].includes(result)) {
    return <Navigate to={`/login?auth=${result}`} replace />;
  }
  return <LandingPage />;
}

function App() {
  return (
    <div className="App">
      <PageErrorBoundary>
        <AuthProvider>
          <UserPrefsProvider>
            <ConversationProvider>
              <VoiceProvider>
                <LiveChatProvider>
                  <LiveLearningProvider>
                    <LiveClaimReviewProvider>
                      <LiveQueueProvider>
                        <LiveGovernedProvider>
                          <BrowserRouter>
                            <Suspense 
                              fallback={
                                <div className="route-loading" role="status" aria-live="polite">
                                  <div className="route-loading-orb"/>
                                  Loading workspaceâ€¦
                                </div>
                              }
                            >
                              <Routes>
                                {/* Public Routes */}
                                <Route path="/" element={<RootPage />} />
                                <Route path="/platform" element={<PlatformPage />} />
                                <Route path="/capabilities" element={<CapabilitiesPage />} />
                                <Route path="/architecture" element={<ArchitecturePage />} />
                                <Route path="/developers" element={<DevelopersPage />} />
                                <Route path="/docs" element={<DocsPage />} />
                                <Route path="/terms" element={<ProjectDocumentPage kind="terms" />} />
                                <Route path="/privacy" element={<ProjectDocumentPage kind="privacy" />} />
                                <Route path="/ai-transparency" element={<ProjectDocumentPage kind="ai-transparency" />} />
                                <Route path="/contact" element={<ContactPage />} />
                                <Route path="/access" element={<LoginPage />} />
                                <Route path="/login" element={<LoginPage />} />
                                <Route path="/auth/callback" element={<Navigate to="/login" replace />} />

                                {/* Authenticated Engineering Workspace Routes */}
                                <Route path="/app" element={<LiveAuthGate><AppShell /></LiveAuthGate>}>
                                  <Route index element={<CommandCenter />} />
                                  <Route path="chat" element={<ChatPage />} />
                                  <Route path="chat/:id" element={<ChatPage />} />
                                  <Route path="documents/:id" element={<PdfWorkspace />} />
                                  <Route path="library" element={<LibraryPage />} />
                                  <Route path="knowledge" element={<KnowledgeExplorer />} />
                                  <Route path="knowledge/review" element={<LiveClaimReviewPage />} />
                                  <Route path="approvals" element={<LiveGovernedPage />} />
                                  <Route path="learning" element={<LiveLearningPage />} />
                                  <Route path="memory" element={<LiveMemoryPage />} />
                                  <Route path="queue" element={<LiveQueuePage />} />
                                  
                                  <Route path="research" element={<ResearchPage />} />
                                  <Route path="analytics" element={mode === "live" ? <LiveOperationsPage kind="analytics" /> : <AnalyticsPage />} />
                                  <Route path="integrations" element={mode === "live" ? <LiveOperationsPage kind="integrations" /> : <IntegrationsPage />} />
                                  <Route path="integrations/:provider" element={mode === "live" ? <LiveOperationsPage kind="integrations" /> : <IntegrationsPage />} />
                                  <Route path="templates" element={<PreviewOnlyFeature name="Templates"><TemplatesPage /></PreviewOnlyFeature>} />
                                  <Route path="agents" element={<PreviewOnlyFeature name="Agent catalog"><AgentsPage /></PreviewOnlyFeature>} />
                                  <Route path="agents/new" element={<PreviewOnlyFeature name="Agent catalog"><AgentsPage /></PreviewOnlyFeature>} />
                                  <Route path="agents/:id" element={<PreviewOnlyFeature name="Agent catalog"><AgentsPage /></PreviewOnlyFeature>} />
                                  <Route path="evaluations" element={<PreviewOnlyFeature name="Evaluations"><EvaluationsPage /></PreviewOnlyFeature>} />
                                  <Route path="evidence" element={<PreviewOnlyFeature name="Evidence qualification"><EvaluationsPage /></PreviewOnlyFeature>} />

                                  <Route path="workflows" element={<PreviewOnlyFeature name="Workflows"><WorkflowsPage /></PreviewOnlyFeature>} />
                                  <Route path="workflows/new" element={<PreviewOnlyFeature name="Workflow studio"><WorkflowStudio /></PreviewOnlyFeature>} />
                                  <Route path="workflows/:id/edit" element={<PreviewOnlyFeature name="Workflow studio"><WorkflowStudio /></PreviewOnlyFeature>} />
                                  <Route path="workflows/:id/versions" element={<PreviewOnlyFeature name="Workflow studio"><WorkflowStudio /></PreviewOnlyFeature>} />
                                  <Route path="models" element={mode === "live" ? <LiveOperationsPage kind="models" /> : <ModelsPage />} />
                                  <Route path="observability" element={mode === "live" ? <LiveOperationsPage kind="observability" /> : <ObservabilityPage />} />
                                  <Route path="costs" element={<CostsPage />} />
                                  <Route path="governance" element={mode === "live" ? <LiveOperationsPage kind="governance" /> : <GovernancePage />} />
                                  <Route path="audit" element={mode === "live" ? <LiveOperationsPage kind="audit" /> : <AuditPage />} />
                                  <Route path="notifications" element={<NotificationsPage />} />
                                  <Route path="settings" element={mode === "live" ? <LiveOperationsPage kind="settings" /> : <SettingsPage />} />
                                  <Route path="developers" element={mode === "live" ? <LiveOperationsPage kind="developers" /> : <ContractsPage />} />
                                  <Route path="executions" element={<PreviewOnlyFeature name="Executions"><ExecutionsPage /></PreviewOnlyFeature>} />
                                  <Route path="executions/:id" element={<PreviewOnlyFeature name="Executions"><ExecutionsPage /></PreviewOnlyFeature>} />
                                  <Route path="demo-controls" element={<PreviewOnlyFeature name="Demo controls"><DemoControlsPage /></PreviewOnlyFeature>} />
                                </Route>

                                <Route path="*" element={<Navigate to="/" replace />} />
                              </Routes>
                            </Suspense>
                          </BrowserRouter>
                        </LiveGovernedProvider>
                      </LiveQueueProvider>
                    </LiveClaimReviewProvider>
                  </LiveLearningProvider>
                </LiveChatProvider>
              </VoiceProvider>
            </ConversationProvider>
          </UserPrefsProvider>
        </AuthProvider>
      </PageErrorBoundary>
      <Toaster theme="dark" position="bottom-right" richColors />
    </div>
  );
}

export default App;
