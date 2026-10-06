import React from 'react';
import { CONFIG } from '../config';

export const TechStack = () => {
  const techs = ["React", "FastAPI", "scikit-learn", "OR-Tools", "Firebase Realtime Database", "Gemini 2.5 Flash"];
  
  return (
    <section id="tech" className="py-24 bg-navy relative border-t border-border">
      <div className="max-w-7xl mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold mb-12">Built With</h2>
        <div className="flex flex-wrap justify-center gap-4 mb-24">
          {techs.map(t => (
            <div key={t} className="px-6 py-3 border border-border rounded-full bg-panel text-text-muted font-mono text-sm hover:border-accent hover:text-text-main transition-colors">
              {t}
            </div>
          ))}
        </div>

        <div className="bg-warn/10 border border-warn/30 text-warn p-4 rounded-md text-sm max-w-3xl mx-auto font-mono">
          <strong>PROTOTYPE NOTICE:</strong> All data is synthetic / simulated for prototype demonstration. Decision-support prototype. Not validated on real aircraft data.
        </div>
      </div>
    </section>
  );
};

export const Footer = () => {
  return (
    <footer className="py-12 bg-panel border-t border-border text-center">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-4xl font-bold mb-8">See the A17 scenario end to end.</h2>
        <div className="flex flex-wrap justify-center gap-4 mb-16">
          <a href={CONFIG.DEMO_URL} className="px-8 py-4 bg-accent text-navy font-bold rounded-md hover:bg-accent/90 transition-colors">
            Launch Demo
          </a>
          <a href={CONFIG.VIDEO_URL} className="px-8 py-4 bg-transparent border border-border text-text-main rounded-md hover:bg-navy transition-colors">
            View Walkthrough
          </a>
        </div>
        
        <div className="text-text-muted text-sm flex flex-col md:flex-row items-center justify-center gap-2 md:gap-8 font-mono">
          <span>Problem Statement: {CONFIG.PROBLEM_STATEMENT}</span>
          <span className="hidden md:inline">•</span>
          <span>Smart India Hackathon 2026</span>
          <span className="hidden md:inline">•</span>
          <span>Team: {CONFIG.TEAM_NAME}</span>
        </div>
      </div>
    </footer>
  );
};
