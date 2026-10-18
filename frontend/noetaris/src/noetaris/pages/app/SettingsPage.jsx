import React, { useState } from 'react';
import { 
  User, Bot, Palette, Sliders, Shield, RefreshCw, Check, 
  Sparkles, FileText, Mic, AlertCircle, Save, Download
} from 'lucide-react';
import { toast } from 'sonner';
import { useUserPrefs } from '../../state/UserPrefsContext';
import Avatar, { BotAvatar, UserAvatar } from '../../components/Avatar';
import { PageHeader } from './OperationsPages';

const GRADIENT_PRESETS = [
  { id: 'blue-red', name: 'Noetaris Dual (Blue & Red)', class: 'from-[#1A6BB5] to-[#C41E2A]', preview: 'bg-gradient-to-r from-[#1A6BB5] to-[#C41E2A]' },
  { id: 'blue-cyan', name: 'Cyan Electric (Blue & Cyan)', class: 'from-[#1A6BB5] to-[#5ED6ED]', preview: 'bg-gradient-to-r from-[#1A6BB5] to-[#5ED6ED]' },
  { id: 'red-amber', name: 'Thermal Ember (Red & Amber)', class: 'from-[#C41E2A] to-[#F2B35E]', preview: 'bg-gradient-to-r from-[#C41E2A] to-[#F2B35E]' },
  { id: 'green-cyan', name: 'Bio Neon (Green & Cyan)', class: 'from-[#48C7A1] to-[#5ED6ED]', preview: 'bg-gradient-to-r from-[#48C7A1] to-[#5ED6ED]' },
  { id: 'purple-pink', name: 'Deep Space (Purple & Pink)', class: 'from-[#8F85E8] to-[#F24F61]', preview: 'bg-gradient-to-r from-[#8F85E8] to-[#F24F61]' },
];

export default function SettingsPage() {
  const { 
    prefs, 
    gradientClass, 
    updateProfile, 
    updateAI, 
    updateAppearance, 
    resetAll 
  } = useUserPrefs();

  const [activeTab, setActiveTab] = useState('profile');
  const [profileForm, setProfileForm] = useState({
    displayName: prefs.displayName,
    initials: prefs.initials,
    role: prefs.role,
    org: prefs.org,
    avatarGradient: prefs.avatarGradient,
  });

  const [aiForm, setAiForm] = useState({
    assistantName: prefs.ai.assistantName,
    responseVerbosity: prefs.ai.responseVerbosity,
    autoCitation: prefs.ai.autoCitation,
    autoDocOpen: prefs.ai.autoDocOpen,
    showConfidence: prefs.ai.showConfidence,
    voiceEnabled: prefs.ai.voiceEnabled,
  });

  const [appearanceForm, setAppearanceForm] = useState({
    fontSize: prefs.appearance.fontSize,
    animationsEnabled: prefs.appearance.animationsEnabled,
    accentColor: prefs.appearance.accentColor,
  });

  const handleSaveProfile = (e) => {
    e?.preventDefault();
    updateProfile(profileForm);
    toast.success('Profile settings updated');
  };

  const handleSaveAI = (e) => {
    e?.preventDefault();
    updateAI(aiForm);
    toast.success('AI Assistant preferences saved');
  };

  const handleSaveAppearance = (e) => {
    e?.preventDefault();
    updateAppearance(appearanceForm);
    toast.success('Appearance settings saved');
  };

  const handleReset = () => {
    if (window.confirm('Reset all preferences to default values?')) {
      resetAll();
      toast.info('Preferences reset to default factory settings');
      setProfileForm({
        displayName: 'Jane Dohen',
        initials: 'JD',
        role: 'Administrator',
        org: 'Nomadic Lab Engineering',
        avatarGradient: 'blue-red',
      });
      setAiForm({
        assistantName: 'Noetaris',
        responseVerbosity: 'balanced',
        autoCitation: true,
        autoDocOpen: true,
        showConfidence: true,
        voiceEnabled: true,
      });
      setAppearanceForm({
        fontSize: 'default',
        animationsEnabled: true,
        accentColor: 'blue',
      });
    }
  };

  const handleExport = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(prefs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', 'noetaris-user-preferences.json');
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    toast.success('Preferences exported to JSON');
  };

  return (
    <div className="p-4 md:p-8 max-w-5xl" data-testid="settings-page">
      <PageHeader 
        title="Settings & Preferences" 
        eyebrow="User · AI Persona · Environment"
        action={
          <div className="flex items-center gap-2">
            <button 
              onClick={handleExport}
              className="n-btn-ghost h-9 px-3 text-xs flex items-center gap-1.5"
              title="Export Preferences"
            >
              <Download size={13} />
              <span>Export</span>
            </button>
            <button 
              onClick={handleReset}
              className="n-btn-ghost h-9 px-3 text-xs flex items-center gap-1.5 text-red-400 hover:text-red-300"
              title="Reset All Preferences"
            >
              <RefreshCw size={13} />
              <span>Reset</span>
            </button>
          </div>
        }
      >
        Customize your engineering persona, AI assistant parameters, citation behavior, and interface styles.
      </PageHeader>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-[color:var(--n-stroke-soft)] mb-6 overflow-x-auto pb-px">
        {[
          { id: 'profile', label: 'User Persona', icon: User },
          { id: 'ai', label: 'AI Assistant', icon: Bot },
          { id: 'appearance', label: 'Theme & Visuals', icon: Palette },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium rounded-t-lg transition-all border-b-2 -mb-px whitespace-nowrap ${
                isActive 
                  ? 'border-[color:var(--n-blue)] text-white bg-white/5 font-semibold' 
                  : 'border-transparent text-[color:var(--n-text-mute)] hover:text-white hover:bg-white/[0.02]'
              }`}
            >
              <Icon size={14} className={isActive ? 'text-[color:var(--n-blue)]' : ''} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab: User Profile */}
      {activeTab === 'profile' && (
        <form onSubmit={handleSaveProfile} className="space-y-6">
          <div className="n-glass rounded-2xl p-6 border border-[color:var(--n-stroke-soft)]">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6 pb-6 border-b border-[color:var(--n-stroke-soft)]">
              {/* Live Preview Avatar */}
              <div className="flex flex-col items-center gap-2">
                <Avatar
                  size="xl"
                  initials={profileForm.initials || '??'}
                  gradient={`bg-gradient-to-br ${GRADIENT_PRESETS.find(g => g.id === profileForm.avatarGradient)?.class || 'from-[#1A6BB5] to-[#C41E2A]'}`}
                  ring
                />
                <span className="text-[10px] uppercase font-mono text-[color:var(--n-text-subtle)]">Avatar Preview</span>
              </div>

              <div className="flex-1 space-y-1">
                <h3 className="text-base font-semibold text-white">{profileForm.displayName || 'Unnamed User'}</h3>
                <p className="text-xs text-[color:var(--n-text-mute)]">
                  {profileForm.role} · {profileForm.org}
                </p>
                <div className="pt-2 text-xs text-[color:var(--n-text-subtle)]">
                  Your initials and gradient represent your messages in the AI conversation threads and the workspace header.
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-6">
              <div>
                <label className="block text-xs font-semibold text-white mb-1.5">Display Name</label>
                <input
                  type="text"
                  value={profileForm.displayName}
                  onChange={(e) => {
                    const name = e.target.value;
                    const parts = name.trim().split(/\s+/);
                    let newInitials = profileForm.initials;
                    if (parts.length >= 2) {
                      newInitials = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
                    } else if (parts.length === 1 && parts[0].length >= 2) {
                      newInitials = parts[0].slice(0, 2).toUpperCase();
                    }
                    setProfileForm(p => ({ ...p, displayName: name, initials: newInitials }));
                  }}
                  className="w-full bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[color:var(--n-blue)]"
                  placeholder="e.g. Jane Dohen"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-white mb-1.5">Initials (Badge)</label>
                <input
                  type="text"
                  maxLength={2}
                  value={profileForm.initials}
                  onChange={(e) => setProfileForm(p => ({ ...p, initials: e.target.value.toUpperCase() }))}
                  className="w-full bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3.5 py-2 text-xs text-white font-mono uppercase tracking-wider placeholder-slate-500 focus:outline-none focus:border-[color:var(--n-blue)]"
                  placeholder="JD"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-white mb-1.5">Engineering Role</label>
                <input
                  type="text"
                  value={profileForm.role}
                  onChange={(e) => setProfileForm(p => ({ ...p, role: e.target.value }))}
                  className="w-full bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[color:var(--n-blue)]"
                  placeholder="e.g. Senior Powertrain Diagnostics Lead"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-white mb-1.5">Organization / Unit</label>
                <input
                  type="text"
                  value={profileForm.org}
                  onChange={(e) => setProfileForm(p => ({ ...p, org: e.target.value }))}
                  className="w-full bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[color:var(--n-blue)]"
                  placeholder="e.g. Nomadic Lab Engineering"
                />
              </div>
            </div>

            {/* Gradient Swatches */}
            <div className="pt-6">
              <label className="block text-xs font-semibold text-white mb-2">Avatar Color Theme</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {GRADIENT_PRESETS.map((preset) => {
                  const isSelected = profileForm.avatarGradient === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => setProfileForm(p => ({ ...p, avatarGradient: preset.id }))}
                      className={`flex items-center gap-3 p-2.5 rounded-xl border text-left transition-all ${
                        isSelected 
                          ? 'bg-white/10 border-[color:var(--n-blue)] ring-1 ring-[color:var(--n-blue)]' 
                          : 'bg-black/20 border-[color:var(--n-stroke-soft)] hover:bg-white/5'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-full ${preset.preview} flex items-center justify-center shrink-0 shadow-sm`}>
                        {isSelected && <Check size={14} className="text-white drop-shadow" />}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-white truncate">{preset.name}</div>
                        <div className="text-[10px] text-[color:var(--n-text-subtle)] font-mono">{preset.id}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="n-btn-primary px-5 py-2 text-xs flex items-center gap-2"
            >
              <Save size={13} />
              <span>Save Profile Changes</span>
            </button>
          </div>
        </form>
      )}

      {/* Tab: AI Assistant Settings */}
      {activeTab === 'ai' && (
        <form onSubmit={handleSaveAI} className="space-y-6">
          <div className="n-glass rounded-2xl p-6 border border-[color:var(--n-stroke-soft)] space-y-6">
            <div className="flex items-center gap-4 pb-4 border-b border-[color:var(--n-stroke-soft)]">
              <BotAvatar size="lg" pulse />
              <div>
                <h3 className="text-base font-semibold text-white">AI Assistant Configuration</h3>
                <p className="text-xs text-[color:var(--n-text-mute)]">
                  Tune how the floating engineering assistant formats answers, anchors citations, and links service manuals.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-white mb-1.5">Assistant Name</label>
                <input
                  type="text"
                  value={aiForm.assistantName}
                  onChange={(e) => setAiForm(p => ({ ...p, assistantName: e.target.value }))}
                  className="w-full bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[color:var(--n-blue)]"
                  placeholder="Noetaris"
                />
                <span className="text-[10px] text-[color:var(--n-text-subtle)] mt-1 block">Displayed on the FAB header and message bubbles.</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-white mb-1.5">Response Verbosity</label>
                <select
                  value={aiForm.responseVerbosity}
                  onChange={(e) => setAiForm(p => ({ ...p, responseVerbosity: e.target.value }))}
                  className="w-full bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-[color:var(--n-blue)]"
                >
                  <option value="concise">Concise — Bulleted technical summaries and page anchors only</option>
                  <option value="balanced">Balanced — Contextual rationale with diagnostic steps</option>
                  <option value="detailed">Detailed — Comprehensive root cause, schematic references & citations</option>
                </select>
              </div>
            </div>

            {/* Feature Toggles */}
            <div className="space-y-3 pt-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-[color:var(--n-text-subtle)]">Document & Grounding Features</div>
              
              {[
                { 
                  k: 'autoDocOpen', 
                  title: 'Auto-Open Service Manual', 
                  desc: 'Automatically open the PDF Manual alongside chat when a citation anchor is mentioned in the answer.' 
                },
                { 
                  k: 'autoCitation', 
                  title: 'Highlight Anchored Spans', 
                  desc: 'Pulse and flash yellow highlight on referenced manual passages when navigating to citations.' 
                },
                { 
                  k: 'showConfidence', 
                  title: 'Show Confidence & Grounding Badges', 
                  desc: 'Display high/medium/verified grounding percentage pills above each AI response.' 
                },
                { 
                  k: 'voiceEnabled', 
                  title: 'Voice Input Support', 
                  desc: 'Enable microphone recording and speech-to-intent in the floating FAB panel.' 
                },
              ].map(toggle => (
                <div key={toggle.k} className="p-3.5 rounded-xl bg-black/20 border border-[color:var(--n-stroke-soft)] flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="text-xs font-medium text-white">{toggle.title}</div>
                    <div className="text-[11px] text-[color:var(--n-text-mute)] mt-0.5">{toggle.desc}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setAiForm(p => ({ ...p, [toggle.k]: !p[toggle.k] }))}
                    className={`w-11 h-6 rounded-full relative transition-colors ${
                      aiForm[toggle.k] ? 'bg-[color:var(--n-blue)]' : 'bg-white/10'
                    }`}
                  >
                    <span 
                      className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                        aiForm[toggle.k] ? 'translate-x-5' : 'translate-x-0'
                      }`} 
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="n-btn-primary px-5 py-2 text-xs flex items-center gap-2"
            >
              <Save size={13} />
              <span>Save AI Settings</span>
            </button>
          </div>
        </form>
      )}

      {/* Tab: Theme & Visuals */}
      {activeTab === 'appearance' && (
        <form onSubmit={handleSaveAppearance} className="space-y-6">
          <div className="n-glass rounded-2xl p-6 border border-[color:var(--n-stroke-soft)] space-y-6">
            <div>
              <h3 className="text-base font-semibold text-white">Theme & Display Styles</h3>
              <p className="text-xs text-[color:var(--n-text-mute)]">
                Control ambient neon glows, animations, and visual scaling.
              </p>
            </div>

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-black/20 border border-[color:var(--n-stroke-soft)] flex items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="text-xs font-medium text-white">Dark-First Mode</div>
                  <div className="text-[11px] text-[color:var(--n-text-mute)] mt-0.5">
                    Noetaris operates in deep chrome/obsidian mode for high-contrast engineering readability. Light surface is reserved for technical document canvases.
                  </div>
                </div>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-[color:var(--n-blue)]/20 text-[color:var(--n-blue)] border border-[color:var(--n-blue)]/40 font-bold">
                  ALWAYS ON
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-black/20 border border-[color:var(--n-stroke-soft)] flex items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="text-xs font-medium text-white">Chrome Seam Light Animations</div>
                  <div className="text-[11px] text-[color:var(--n-text-mute)] mt-0.5">
                    Enable the polished metallic chrome N-symbol with dual-side blue & red neon seam glows.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setAppearanceForm(p => ({ ...p, animationsEnabled: !p.animationsEnabled }))}
                  className={`w-11 h-6 rounded-full relative transition-colors ${
                    appearanceForm.animationsEnabled ? 'bg-[color:var(--n-blue)]' : 'bg-white/10'
                  }`}
                >
                  <span 
                    className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                      appearanceForm.animationsEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`} 
                  />
                </button>
              </div>

              <div className="p-3.5 rounded-xl bg-black/20 border border-[color:var(--n-stroke-soft)] flex items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="text-xs font-medium text-white">Font Density</div>
                  <div className="text-[11px] text-[color:var(--n-text-mute)] mt-0.5">
                    Adjust text scaling across tables, inspector panels, and chat threads.
                  </div>
                </div>
                <select
                  value={appearanceForm.fontSize}
                  onChange={(e) => setAppearanceForm(p => ({ ...p, fontSize: e.target.value }))}
                  className="bg-[#050B14]/80 border border-[color:var(--n-stroke-soft)] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[color:var(--n-blue)]"
                >
                  <option value="compact">Compact (High density)</option>
                  <option value="default">Default (Balanced)</option>
                  <option value="large">Spacious (Accessibility)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="n-btn-primary px-5 py-2 text-xs flex items-center gap-2"
            >
              <Save size={13} />
              <span>Save Appearance Changes</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
