import React, { useState } from 'react';
import { motion } from 'framer-motion';

const STRATEGIES = [
  { id: 'repair', label: 'Repair Now', downtime: 4, risk: 10, avail: 92, best: false },
  { id: 'defer6', label: 'Defer 6h', downtime: 4, risk: 25, avail: 88, best: false },
  { id: 'bundle', label: 'Bundle w/ Sched. Inspection', downtime: 2.5, risk: 15, avail: 96, best: true },
  { id: 'defer24', label: 'Defer 24h', downtime: 8, risk: 85, avail: 75, best: false },
];

export const WhatIfSimulator = () => {
  const [active, setActive] = useState(STRATEGIES[2]);

  return (
    <section className="py-24 bg-navy relative border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-bold mb-4">Interactive Simulator</h2>
          <p className="text-text-muted">Simulate the cascading effects of maintenance decisions. <span className="italic opacity-50">(Illustrative sample data)</span></p>
        </div>

        <div className="glass-panel p-8 rounded-xl max-w-4xl mx-auto border-accent/20 shadow-[0_0_40px_rgba(74,163,223,0.05)]">
          <div className="flex flex-wrap gap-2 mb-10 justify-center">
            {STRATEGIES.map(s => (
              <button 
                key={s.id}
                onClick={() => setActive(s)}
                className={`px-4 py-2 rounded font-mono text-sm border transition-all ${
                  active.id === s.id 
                    ? 'bg-accent/20 border-accent text-accent' 
                    : 'bg-panel border-border text-text-muted hover:border-accent/50'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="space-y-2">
              <div className="text-xs text-text-muted font-mono uppercase tracking-wider">Expected Downtime</div>
              <div className="text-4xl font-bold font-sans">{active.downtime}h</div>
              <div className="w-full bg-panel h-2 rounded overflow-hidden mt-4">
                <motion.div 
                  className="h-full bg-accent" 
                  initial={{ width: 0 }}
                  animate={{ width: `${(active.downtime / 8) * 100}%` }}
                  transition={{ type: "spring", stiffness: 100 }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-text-muted font-mono uppercase tracking-wider">Failure Risk</div>
              <div className={`text-4xl font-bold font-sans ${active.risk > 50 ? 'text-crit' : active.risk > 20 ? 'text-warn' : 'text-ok'}`}>{active.risk}%</div>
              <div className="w-full bg-panel h-2 rounded overflow-hidden mt-4">
                <motion.div 
                  className={`h-full ${active.risk > 50 ? 'bg-crit' : active.risk > 20 ? 'bg-warn' : 'bg-ok'}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${active.risk}%` }}
                  transition={{ type: "spring", stiffness: 100 }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-text-muted font-mono uppercase tracking-wider">Fleet Avail. Impact</div>
              <div className="text-4xl font-bold font-sans text-text-main">{active.avail}%</div>
              <div className="w-full bg-panel h-2 rounded overflow-hidden mt-4">
                <motion.div 
                  className="h-full bg-ok" 
                  initial={{ width: 0 }}
                  animate={{ width: `${active.avail}%` }}
                  transition={{ type: "spring", stiffness: 100 }}
                />
              </div>
            </div>
          </div>

          <div className="mt-10 p-4 rounded bg-panel border border-border flex items-center justify-between">
            <div>
              <span className="text-xs text-text-muted font-mono block mb-1">Recommendation</span>
              {active.best ? (
                <span className="text-ok font-bold">✓ Optimal: Bundling reduces overall downtime and preserves fleet readiness.</span>
              ) : (
                <span className="text-warn font-bold">⚠ Suboptimal: {active.risk > 50 ? 'Risk of catastrophic failure too high.' : 'Results in unnecessary ground time.'}</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
