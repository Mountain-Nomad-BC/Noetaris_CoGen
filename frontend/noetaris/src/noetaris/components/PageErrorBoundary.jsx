import React from 'react';
export default class PageErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('NOETARIS page error', error, info.componentStack); }
  render() {
    if (this.state.error) return <main role="alert" className="min-h-[45vh] flex items-center justify-center p-8">
      <div className="n-glass rounded-2xl p-8 max-w-lg w-full">
        <h1 className="font-display text-2xl mb-3">This view could not load.</h1>
        <p className="text-sm text-[color:var(--n-text-mute)] mb-5">The rest of the workspace is still available. This screen hit an unexpected UI error.</p>
        <button className="n-cta px-5 py-3 text-sm" onClick={() => { this.setState({ error: null }); window.location.reload(); }}>Reload view</button>
      </div>
    </main>;
    return this.props.children;
  }
}
