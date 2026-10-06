import React from 'react';
import { motion } from 'framer-motion';

export const Problem = () => {
  return (
    <section id="problem" className="py-24 bg-navy relative border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-16">
          <h2 className="text-3xl font-bold mb-4">The Challenge</h2>
          <p className="text-text-muted max-w-2xl">
            Air fleets suffer from fragmented data, reactive maintenance, and avoidable downtime. 
            Addressing Problem Statement 26249, we need to move from reactive repairs to predictive, optimized scheduling.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-24">
          {[
            { title: "Fragmented Data", desc: "Sensors, maintenance logs, and spare inventory live in silos." },
            { title: "Reactive Maintenance", desc: "Unexpected failures ground aircraft, causing cascading schedule disruptions." },
            { title: "Suboptimal Planning", desc: "Without holistic optimization, technicians and bays are inefficiently allocated." }
          ].map((stat, i) => (
            <motion.div 
              key={i}
              className="glass-panel p-6 rounded-lg"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <h3 className="text-lg font-bold text-accent mb-2">{stat.title}</h3>
              <p className="text-sm text-text-muted">{stat.desc}</p>
            </motion.div>
          ))}
        </div>

        <div>
          <h3 className="text-2xl font-bold mb-8 text-center">Conventional vs VAYU-NETRA</h3>
          <div className="grid md:grid-cols-2 gap-12">
            <div className="glass-panel p-8 rounded-lg border-border">
              <div className="text-sm font-mono text-text-muted mb-6 uppercase tracking-wider">Conventional Approach</div>
              <ul className="space-y-4">
                <li className="flex items-center gap-3 text-text-muted"><span className="w-2 h-2 rounded-full bg-border"></span> Sensor Data</li>
                <li className="flex items-center gap-3 text-text-muted"><span className="w-2 h-2 rounded-full bg-border"></span> Failure Prediction</li>
                <li className="flex items-center gap-3 text-crit"><span className="w-2 h-2 rounded-full bg-crit"></span> Alert (Reactive)</li>
              </ul>
            </div>
            
            <div className="glass-panel p-8 rounded-lg border-accent/30 relative overflow-hidden">
              <div className="absolute inset-0 bg-accent/5"></div>
              <div className="relative z-10">
                <div className="text-sm font-mono text-accent mb-6 uppercase tracking-wider">VAYU-NETRA Approach</div>
                <ul className="space-y-4">
                  <li className="flex items-center gap-3 text-text-main"><span className="w-2 h-2 rounded-full bg-ok"></span> Data Fusion</li>
                  <li className="flex items-center gap-3 text-text-main"><span className="w-2 h-2 rounded-full bg-ok"></span> Health & RUL Prediction</li>
                  <li className="flex items-center gap-3 text-text-main"><span className="w-2 h-2 rounded-full bg-accent"></span> Fleet Impact Scoring</li>
                  <li className="flex items-center gap-3 text-text-main"><span className="w-2 h-2 rounded-full bg-accent"></span> What-If Simulation</li>
                  <li className="flex items-center gap-3 text-text-main"><span className="w-2 h-2 rounded-full bg-accent"></span> Resource Optimization</li>
                  <li className="flex items-center gap-3 text-accent font-bold"><span className="w-2 h-2 rounded-full bg-accent text-glow animate-pulse"></span> Recommended Action</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
