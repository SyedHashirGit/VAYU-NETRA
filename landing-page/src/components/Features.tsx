import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Brain, Box, Bell, Database, Users, ShieldAlert, Cpu } from 'lucide-react';

const FEATURE_LIST = [
  { id: 'fcc', icon: <Database />, title: 'Fleet Command Center', desc: 'KPIs and aircraft ranked dynamically by their fleet impact score.' },
  { id: 'dt', icon: <Box />, title: 'Aircraft Digital Twin', desc: 'Component tree with real-time health, failure probability, and RUL.' },
  { id: 'pm', icon: <Activity />, title: 'Predictive Maintenance', desc: 'Isolation Forest anomaly detection and gradient-boosting failure probability.' },
  { id: 'opt', icon: <Cpu />, title: 'Maintenance Optimizer', desc: 'Google OR-Tools solver accounting for technician skills, bays, and spares.' },
  { id: 'xai', icon: <Brain />, title: 'Explainable AI', desc: 'Transparent risk drivers per component (e.g., vibration, temp drift).' },
  { id: 'al', icon: <ShieldAlert />, title: 'Intelligent Alerts', desc: 'Proactive notifications for abnormal telemetry or spare shortages.' },
  { id: 'res', icon: <Users />, title: 'Resource Management', desc: 'Live tracking of shortage risks, bottlenecks, and bay reservations.' },
  { id: 'llm', icon: <Bell />, title: 'AI Copilot', desc: 'Gemini 2.5 Flash integrated with backend function calling for direct data queries.' },
];

export const Features = () => {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <section id="features" className="py-24 bg-panel relative border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-3xl font-bold mb-12 text-center">Core Capabilities</h2>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURE_LIST.map((feat) => (
            <motion.div 
              key={feat.id}
              className={`glass-panel p-6 rounded-lg cursor-pointer transition-all duration-300 ${expanded === feat.id ? 'border-accent shadow-[0_0_20px_rgba(74,163,223,0.15)] scale-[1.02] z-10 relative' : 'border-border hover:border-accent/50 hover:bg-navy/50'}`}
              onClick={() => setExpanded(expanded === feat.id ? null : feat.id)}
              layout
            >
              <div className="text-accent mb-4">{feat.icon}</div>
              <h3 className="font-bold text-text-main mb-2">{feat.title}</h3>
              
              {expanded === feat.id ? (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="text-sm text-text-muted mt-4 border-t border-border/50 pt-4"
                >
                  {feat.desc}
                </motion.div>
              ) : (
                <p className="text-sm text-text-muted line-clamp-2">{feat.desc}</p>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
