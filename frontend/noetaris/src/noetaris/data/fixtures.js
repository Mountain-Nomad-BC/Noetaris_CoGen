// NOETARIS CoGen demo fixtures. ALL data here is DEMO_FIXTURE.
// Never render as real backend truth. See contracts/API_CONTRACT_REGISTER.md

export const brand = {
  product: "Noetaris CoGen",
  org: "Nomadic Lab Engineering",
  engine: "NSAI",
  tagline: "Engineering Intelligence, grounded in your sources.",
};

export const navDomains = [
  {
    key: "intelligence",
    label: "Intelligence",
    items: [
      { to: "/app", label: "Command Center", icon: "LayoutDashboard" },
      { to: "/app/chat", label: "Conversations", icon: "MessagesSquare" },
      { to: "/app/library", label: "Document Library", icon: "Library" },
      { to: "/app/documents/doc-1", label: "Evidence Viewer", icon: "FileSearch" },
      { to: "/app/knowledge", label: "Knowledge Explorer", icon: "Share2" },
      { to: "/app/knowledge/review", label: "Knowledge Review", icon: "ShieldCheck" },
      { to: "/app/research", label: "Research Workspace", icon: "FlaskConical" },
      { to: "/app/memory", label: "Memory / Learning", icon: "BrainCircuit" },
      { to: "/app/analytics", label: "Analytics", icon: "LineChart" },
    ],
  },
  {
    key: "build",
    label: "Build",
    items: [
      { to: "/app/agents", label: "Agent Catalog", icon: "Bot" },
      { to: "/app/workflows", label: "Workflow Catalog", icon: "Workflow" },
      { to: "/app/workflows/wf-sample/edit", label: "Workflow Studio", icon: "Hexagon" },
      { to: "/app/templates", label: "Templates", icon: "LayoutTemplate" },
      { to: "/app/executions", label: "Executions / Debugger", icon: "Activity" },
      { to: "/app/queue", label: "Task Queue", icon: "ListChecks" },
    ],
  },
  {
    key: "operate",
    label: "Operate",
    items: [
      { to: "/app/models", label: "Model Routing", icon: "Cpu" },
      { to: "/app/integrations", label: "Providers / Integrations", icon: "Plug" },
      { to: "/app/observability", label: "Observability", icon: "Radar" },
      { to: "/app/costs", label: "Cost / Usage", icon: "Coins" },
      { to: "/app/governance", label: "Governance", icon: "Scale" },
      { to: "/app/audit", label: "Audit / Approvals", icon: "FileCheck2" },
      { to: "/app/evaluations", label: "Evaluations", icon: "TestTube" },
      { to: "/app/evidence", label: "Evidence / Qualification", icon: "Stamp" },
    ],
  },
  {
    key: "account",
    label: "Account",
    items: [
      { to: "/app/notifications", label: "Notifications", icon: "Bell" },
      { to: "/app/settings", label: "Settings", icon: "Settings" },
      { to: "/app/demo-controls", label: "Demo Controls", icon: "ToggleRight" },
      { to: "/app/developers", label: "Developers", icon: "Code2" },
    ],
  },
];

export const demoKPIs = [
  { label: "Active Agents", value: 24, delta: "+3", trend: [2,3,4,3,5,6,7,6,8,9,10,12] },
  { label: "Workflows Running", value: 7, delta: "+2", trend: [1,2,2,3,4,3,5,6,5,6,7,7] },
  { label: "Tasks in Queue", value: 42, delta: "-9", trend: [60,55,52,50,48,47,46,45,44,43,42,42] },
  { label: "Model Requests / min", value: "3.1K", delta: "+12%", trend: [100,120,140,160,180,200,220,240,260,270,290,310] },
];

export const demoConversation = {
  id: "conv-1",
  title: "Rack integration guide review",
  messages: [
    { id: "m1", role: "user", at: "11:04", text: "Summarize the installation requirements on page 8 and verify them against the power spec on page 12." },
    { id: "m2", role: "assistant", at: "11:04", text:
      "Page 8 requires a level, anchored raised floor with 1200 mm front service clearance. Page 12 specifies 900 mm rear clearance for hot-aisle containment, which conflicts with the 600 mm figure in revision 3. I've flagged the conflict and attached citations.",
      citations: [
        { id: "c1", page: 8, source: "DEMO_FIXTURE_rack_guide.pdf", quote: "Rack must be anchored on a level raised floor with 1200 mm front service clearance." },
        { id: "c2", page: 12, source: "DEMO_FIXTURE_rack_guide.pdf", quote: "Minimum 900 mm rear clearance for hot-aisle containment." },
      ],
    },
    { id: "m3", role: "user", at: "11:05", text: "Flag the conflict in the review queue and open an evidence task." },
  ],
};

export const demoPdfPages = [
  "Cover", "Safety overview", "Specifications", "Component map", "Install sequence", "Clearances",
  "Power distribution", "Installation", "Anchoring", "Service access", "Diagnostics", "Power connections",
].map((title, i) => ({ page: i + 1, title }));

export const demoDoc = {
  name: "DEMO_FIXTURE_rack_guide.pdf",
  rev: 4,
  answer: "Page 8 requires a level anchored floor with 1200 mm front clearance, a dedicated 3-phase feed, a pressure-tested coolant loop and seismic bracing. Citations below jump to the exact anchored span.",
  requirements: [
    { t: "Level anchored floor", p: 8 }, { t: "1200 mm front clearance", p: 6 }, { t: "Dedicated 3-phase feed", p: 12 },
    { t: "Coolant loop pressure test", p: 7 }, { t: "Seismic bracing", p: 9 },
  ],
  citations: [{ t: "Installation", p: 8 }, { t: "Service access", p: 10 }, { t: "Power connections", p: 12 }, { t: "Anchoring", p: 9, uncertain: true }],
  pages: {
    default: { intro: "Diagrammatic placeholder page. In a wired build PDF.js renders the authorized source bytes with exact page geometry, selection anchors and overlays. No private corpus is used in this designer environment.", body: "Select any text on this page to open the evidence toolbar." },
    6: { intro: "Clearances are measured from the outermost rack surface including door swing.", cite: "Maintain 1200 mm front service clearance and 900 mm rear clearance at all times.", body: "Overhead cable trays require 300 mm vertical separation from sprinkler heads." },
    7: { intro: "Liquid-cooling loops are commissioned before power-on.", cite: "Coolant loop must hold 1.5x operating pressure for 30 minutes without decay.", body: "Record test results in the commissioning ledger before energizing." },
    8: { intro: "Installation begins only after site survey sign-off.", cite: "Rack must be anchored on a level raised floor with 1200 mm front service clearance.", body: "Use the supplied leveling feet; maximum floor deviation is 2 mm per metre. Each rack requires a dedicated 3-phase supply and compliant exhaust ventilation." },
    9: { intro: "Anchoring hardware depends on floor type and seismic zone.", body: "Seismic bracing kit S-4 is required in zones 3 and 4.", ocrLow: true },
    10: { intro: "Service access must be preserved for hot-swap components.", cite: "Front and rear doors must open fully to 110° without obstruction.", body: "Blanking panels are mandatory in all unused U positions." },
    12: { intro: "Power connections are made by a qualified electrician.", cite: "Each rack requires a dedicated 3-phase 32 A feed with separate A/B paths.", body: "Minimum 900 mm rear clearance for hot-aisle containment. Revision 3 listed 600 mm and is superseded." },
  },
};

export const demoAuditLog = Array.from({ length: 14 }).map((_, i) => ({
  id: "ev-" + (i + 1),
  at: new Date(Date.now() - i * 1000 * 60 * 7).toISOString(),
  actor: ["jd@nomadic.lab", "svc.agent.research-01", "svc.workflow.exec", "ops@nomadic.lab"][i % 4],
  action: [
    "signed in via local token",
    "ran workflow revision wf.rev.37",
    "approved knowledge candidate kc-882",
    "revoked source doc-7 revision 4",
    "edited agent agt.research-01",
    "paused workflow wf-sample",
    "updated budget cap",
  ][i % 7],
  scope: ["identity","workflow","knowledge","source","agent","workflow","budget"][i % 7],
  status: i % 5 === 0 ? "LIVE_RESTRICTED" : "LIVE_VERIFIED",
}));

export const demoAgents = [
  { id: "agt.research-01", name: "Research Agent", role: "Research", status: "Running", util: 72, model: "GPT-5 reserved" },
  { id: "agt.analyst-03",  name: "Data Analyst",   role: "Analysis", status: "Running", util: 64, model: "Claude Sonnet 5" },
  { id: "agt.code-02",     name: "Code Agent",     role: "Development", status: "Idle",    util: 12, model: "Gemini 3 Flash" },
  { id: "agt.train-01",    name: "ML Trainer",     role: "Training", status: "Running", util: 81, model: "Local / AMD" },
  { id: "agt.ops-04",      name: "Ops Agent",      role: "Operations", status: "Error",   util: 0,  model: "GPT-5" },
  { id: "agt.sec-01",      name: "Security Agent", role: "Security", status: "Running", util: 55, model: "Claude Haiku 4.5" },
];

export const demoWorkflows = [
  { id: "wf-1", name: "Ingest & process documents", progress: 78, eta: "2m 14s", color: "blue" },
  { id: "wf-2", name: "Multi-agent evidence pipeline", progress: 42, eta: "5m 21s", color: "red" },
  { id: "wf-3", name: "Generate insights", progress: 91, eta: "1m 03s", color: "blue" },
  { id: "wf-4", name: "Human review stage", progress: 12, eta: "8m 44s", color: "amber" },
  { id: "wf-5", name: "Publish results", progress: 0, eta: "queued", color: "muted" },
];

export const demoModels = [
  { name: "OpenAI GPT-5 / Terra", pct: 38, rpm: "4.7K req/min", color: "#2E9BFF" },
  { name: "Anthropic Claude Sonnet 5.5", pct: 24, rpm: "2.9K req/min", color: "#5ED6ED" },
  { name: "Google Gemini 3 Flash", pct: 16, rpm: "1.8K req/min", color: "#8F85E8" },
  { name: "Meta Llama 3.1", pct: 12, rpm: "1.4K req/min", color: "#F2B35E" },
  { name: "Mistral 8x7B", pct: 6, rpm: "682 req/min", color: "#48C7A1" },
  { name: "Cohere Command R+", pct: 4, rpm: "391 req/min", color: "#F24F61" },
];

export const demoCosts = {
  period: "Last 30 days",
  spend: 2847.42,
  cap: 5000.0,
  byProvider: [
    { label: "OpenAI", value: 1240 },
    { label: "Anthropic", value: 802 },
    { label: "Google", value: 410 },
    { label: "Local / AMD", value: 220 },
    { label: "Other", value: 175 },
  ],
  daily: Array.from({length: 30}).map((_,i)=> ({ d: i+1, v: Math.round(60 + Math.sin(i/3)*22 + i*2.1) })),
};

export const demoNotifications = [
  { id:"n1", kind:"info", title:"Workflow wf-sample paused", at:"2m ago" },
  { id:"n2", kind:"warn", title:"Model routing threshold reached", at:"8m ago" },
  { id:"n3", kind:"ok",   title:"Knowledge candidate kc-991 approved", at:"23m ago" },
  { id:"n4", kind:"err",  title:"Ops Agent error — provider timeout", at:"41m ago" },
];
