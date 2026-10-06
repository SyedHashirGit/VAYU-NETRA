import React from 'react';
import { motion } from 'framer-motion';
import { CONFIG } from '../config';
import { Activity } from 'lucide-react';

export const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16 bg-grid">
      <div className="absolute inset-0 bg-gradient-to-b from-navy/50 to-navy z-0"></div>
      
      <div className="max-w-7xl mx-auto px-6 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        <div className="max-w-2xl">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/30 bg-accent/10 text-accent text-xs font-mono mb-6">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
              Decision-Support Prototype SIH 26249
            </div>
            <h1 className="text-5xl md:text-7xl font-sans font-bold leading-tight mb-6">
              Predict failures.<br/>
              Simulate consequences.<br/>
              <span className="text-accent text-glow">Prescribe the optimal action.</span>
            </h1>
            <p className="text-lg text-text-muted mb-8 max-w-xl leading-relaxed">
              We go beyond isolated failure predictions. VAYU-NETRA calculates fleet-wide impact and recommends maintenance strategies that maximize operational availability under real constraints.
            </p>
            <div className="flex flex-wrap gap-4">
              <a href={CONFIG.DEMO_URL} className="px-6 py-3 bg-accent text-navy font-bold rounded-md hover:bg-accent/90 transition-colors flex items-center gap-2">
                Launch Demo
              </a>
              <a href={CONFIG.VIDEO_URL} className="px-6 py-3 bg-transparent border border-border text-text-main rounded-md hover:bg-panel transition-colors">
                Watch Walkthrough
              </a>
            </div>
          </motion.div>
        </div>

        <div className="relative h-[400px] w-full hidden lg:flex items-center justify-center">
          <div className="absolute inset-0 border border-border rounded-full opacity-20 animate-[spin_10s_linear_infinite]"></div>
          <div className="absolute inset-10 border border-border rounded-full opacity-40 animate-[spin_15s_linear_infinite_reverse]"></div>
          
          <div className="grid grid-cols-6 gap-4 relative z-10">
            {Array.from({ length: 30 }).map((_, i) => (
              <motion.div
                key={i}
                className={`w-3 h-3 rounded-full ${i === 16 ? 'bg-crit animate-ping' : i % 5 === 0 ? 'bg-warn' : 'bg-ok opacity-50'}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
              />
            ))}
          </div>

        </div>
      </div>
    </section>
  );
};
