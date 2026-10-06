import React from 'react';
import { CONFIG } from '../config';

export const Nav = () => {
  return (
    <nav className="fixed top-0 w-full z-50 glass-panel border-b border-border/50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-accent/20 border border-accent flex items-center justify-center text-accent font-bold">
            VN
          </div>
          <span className="font-sans font-bold text-lg tracking-widest text-text-main">
            VAYU-<span className="text-accent text-glow">NETRA</span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-text-muted">
          <a href="#problem" className="hover:text-text-main transition-colors">Problem</a>
          <a href="#how-it-works" className="hover:text-text-main transition-colors">How it works</a>
          <a href="#features" className="hover:text-text-main transition-colors">Features</a>
          <a href="#demo" className="hover:text-text-main transition-colors">Demo</a>
          <a href="#tech" className="hover:text-text-main transition-colors">Tech</a>
        </div>
        <div>
          <a href={CONFIG.DEMO_URL} className="bg-accent/10 border border-accent/50 text-accent hover:bg-accent/20 px-4 py-2 rounded-md font-mono text-xs transition-colors">
            Launch Demo
          </a>
        </div>
      </div>
    </nav>
  );
};
