import React from 'react';
import { Link } from 'react-router-dom';
export default function PublicFooter() {
 return <footer className="border-t border-[color:var(--n-stroke-soft)] px-5 py-8 text-sm text-[color:var(--n-text-mute)]">
  <nav aria-label="Documentation and legal" className="flex flex-wrap justify-center gap-5">
   <Link to="/docs">Documentation</Link><Link to="/terms">Terms</Link><Link to="/privacy">Privacy</Link><Link to="/ai-transparency">AI transparency</Link>
  </nav><p className="text-center mt-4">Noetaris CoGen - Research candidate. AI outputs require source verification.</p>
 </footer>;
}
