import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const STAGES = [
  { title: "Data Ingestion", desc: "Aggregates telemetry, maintenance logs, and spare inventory in real-time." },
  { title: "Anomaly Detection", desc: "Isolation Forest models identify abnormal vibration and temperature drift." },
  { title: "Prediction", desc: "Gradient boosting estimates Remaining Useful Life (RUL) and failure probability." },
  { title: "Fleet Impact", desc: "Calculates the cascading effect of a failure on operational readiness." },
  { title: "What-If Simulation", desc: "Models consequences of deferring repairs vs immediate action." },
  { title: "Optimization", desc: "OR-Tools schedules tasks based on technicians, bays, and spares." },
  { title: "Decision", desc: "Recommends the path that maximizes overall fleet availability." },
  { title: "Action", desc: "Reserves spares and assigns work orders automatically." }
];

export const HowItWorks = () => {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStage(prev => (prev + 1) % STAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="how-it-works" className="py-24 bg-panel relative border-t border-border overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-3xl font-bold mb-16">The Pipeline</h2>
        
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="relative border-l-2 border-border pl-8 space-y-8 py-8">
            {STAGES.map((stage, i) => (
              <div key={i} className="relative">
                {/* Timeline dot */}
                <div className={`absolute -left-[41px] top-1 w-5 h-5 rounded-full border-4 border-panel transition-colors duration-500 ${activeStage === i ? 'bg-accent' : 'bg-border'}`}></div>
                
                <div className={`transition-opacity duration-500 ${activeStage === i ? 'opacity-100' : 'opacity-40'}`}>
                  <h3 className={`text-xl font-bold mb-1 ${activeStage === i ? 'text-accent' : 'text-text-main'}`}>{stage.title}</h3>
                  <p className="text-sm text-text-muted">{stage.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="h-[400px] w-full glass-panel rounded-xl flex items-center justify-center p-8 relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeStage}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.1 }}
                transition={{ duration: 0.5 }}
                className="text-center"
              >
                <div className="w-48 h-48 mx-auto mb-6 relative">
                  {/* Abstract representations of stages */}
                  {activeStage === 0 && <div className="absolute inset-0 border-4 border-dashed border-accent rounded-full animate-[spin_10s_linear_infinite]"></div>}
                  {activeStage === 1 && <div className="absolute inset-0 border-4 border-warn rounded-full animate-pulse"></div>}
                  {activeStage === 2 && (
                    <div className="w-full h-full flex items-end justify-between px-4 pb-4">
                      {[40, 60, 30, 80, 20].map((h, i) => <div key={i} style={{height: `${h}%`}} className="w-4 bg-accent/50 rounded-t"></div>)}
                    </div>
                  )}
                  {activeStage === 3 && <div className="absolute inset-4 border-2 border-crit rounded-lg shadow-[0_0_20px_rgba(229,83,61,0.5)]"></div>}
                  {activeStage === 4 && <div className="absolute inset-0 border-4 border-accent rounded flex items-center justify-center font-mono text-2xl">?</div>}
                  {activeStage === 5 && (
                    <div className="w-full h-full flex flex-col justify-center gap-2 px-4">
                       <div className="h-4 bg-ok/80 w-3/4 rounded"></div>
                       <div className="h-4 bg-ok/80 w-1/2 ml-4 rounded"></div>
                       <div className="h-4 bg-ok/80 w-2/3 ml-2 rounded"></div>
                    </div>
                  )}
                  {activeStage === 6 && <div className="absolute inset-0 bg-ok/20 border-2 border-ok rounded-full flex items-center justify-center text-ok font-bold text-3xl">✓</div>}
                  {activeStage === 7 && <div className="absolute inset-0 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>}
                </div>
                <h4 className="text-xl font-mono text-accent">{STAGES[activeStage].title}</h4>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
};
