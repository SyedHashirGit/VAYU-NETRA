import React from 'react';
import { motion } from 'framer-motion';

export const Architecture = () => {
  return (
    <section className="py-24 bg-panel relative border-t border-border">
      <div className="max-w-7xl mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold mb-16">System Architecture</h2>
        
        <div className="glass-panel p-8 rounded-xl border-border inline-block relative">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 md:gap-12 items-center relative z-10">
            
            {/* Input */}
            <div className="flex flex-col gap-4">
              <div className="px-4 py-2 border border-border rounded bg-navy text-sm">Telemetry</div>
              <div className="px-4 py-2 border border-border rounded bg-navy text-sm">Records</div>
            </div>

            <div className="hidden md:block text-accent">→</div>

            {/* Backend / ML */}
            <div className="flex flex-col gap-4">
              <div className="px-4 py-4 border border-accent/50 rounded bg-accent/10 font-bold text-accent shadow-[0_0_15px_rgba(74,163,223,0.1)]">ML Pipeline<br/><span className="text-xs font-normal text-text-muted">FastAPI + scikit-learn</span></div>
              <div className="px-4 py-2 border border-border rounded bg-navy text-sm">Fleet Impact</div>
              <div className="px-4 py-2 border border-border rounded bg-navy text-sm">OR-Tools Optimizer</div>
            </div>

            <div className="hidden md:block text-accent">→</div>

            {/* Output / UI */}
            <div className="flex flex-col gap-4">
              <div className="px-4 py-4 border border-border rounded bg-navy font-bold text-text-main relative group cursor-pointer hover:border-accent">
                React UI
                <div className="absolute hidden group-hover:block bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 p-2 bg-panel border border-border rounded text-xs text-text-muted z-20 shadow-xl">
                  Single page app, Vite, Tailwind, Framer Motion, Three.js
                </div>
              </div>
              <div className="px-4 py-2 border border-border rounded bg-navy text-sm text-mu">Firebase DB</div>
              <div className="px-4 py-2 border border-border rounded bg-navy text-sm text-mu flex items-center justify-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span> Gemini AI
              </div>
            </div>

          </div>
          
          {/* Decorative connection lines behind */}
          <div className="absolute top-1/2 left-0 w-full h-[1px] bg-border -z-0 hidden md:block"></div>
        </div>
      </div>
    </section>
  );
};
