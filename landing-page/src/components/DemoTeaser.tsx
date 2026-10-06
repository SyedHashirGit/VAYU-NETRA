import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export const DemoTeaser = () => {
  const [live, setLive] = useState(false);
  const [health, setHealth] = useState(88);
  const [risk, setRisk] = useState(12);

  useEffect(() => {
    let int: any;
    if (live) {
      int = setInterval(() => {
        setHealth(h => Math.max(10, h - Math.random() * 5));
        setRisk(r => Math.min(99, r + Math.random() * 8));
      }, 800);
    } else {
      setHealth(88);
      setRisk(12);
    }
    return () => clearInterval(int);
  }, [live]);

  return (
    <section id="demo" className="py-24 bg-navy relative border-t border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">See It In Action</h2>
          <p className="text-text-muted">A live degradation simulation shows how data flows through the entire pipeline.</p>
        </div>

        <div className="max-w-3xl mx-auto glass-panel p-6 rounded-xl border-border relative overflow-hidden">
          <div className="absolute top-4 right-6 text-[10px] font-mono text-text-muted opacity-50">INTERACTIVE PREVIEW</div>
          
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-border/50">
            <span className="font-bold text-lg">Fleet Command Center</span>
            <label className="flex items-center gap-2 cursor-pointer">
              <span className="text-sm font-mono text-text-muted">Start live simulation</span>
              <div className={`w-12 h-6 rounded-full p-1 transition-colors ${live ? 'bg-crit' : 'bg-border'}`} onClick={() => setLive(!live)}>
                <motion.div 
                  className="w-4 h-4 bg-white rounded-full" 
                  animate={{ x: live ? 24 : 0 }}
                />
              </div>
            </label>
          </div>

          <table className="w-full text-left text-sm font-mono mb-8">
            <thead>
              <tr className="text-text-muted border-b border-border">
                <th className="pb-2">Rank</th>
                <th className="pb-2">Aircraft</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Health</th>
                <th className="pb-2">Failure Risk</th>
              </tr>
            </thead>
            <tbody>
              <motion.tr layout className={`border-b border-border/20 ${live && risk > 60 ? 'bg-crit/10' : ''}`}>
                <td className="py-3">{live && risk > 60 ? '#1' : '#14'}</td>
                <td className="py-3 font-bold">A17</td>
                <td className="py-3"><span className={`px-2 py-1 rounded text-xs ${live && risk > 60 ? 'bg-crit/20 text-crit' : 'bg-ok/20 text-ok'}`}>{live && risk > 60 ? 'CRITICAL' : 'READY'}</span></td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    {health.toFixed(1)}% 
                    <div className="w-16 h-1 bg-border rounded overflow-hidden"><div className="h-full bg-ok" style={{ width: `${health}%`, backgroundColor: health < 40 ? 'var(--color-crit)' : 'var(--color-ok)' }}></div></div>
                  </div>
                </td>
                <td className={`py-3 ${live && risk > 60 ? 'text-crit font-bold' : ''}`}>{risk.toFixed(1)}%</td>
              </motion.tr>
              <tr className="border-b border-border/20 text-text-muted">
                <td className="py-3">{live && risk > 60 ? '#2' : '#1'}</td>
                <td className="py-3">A04</td>
                <td className="py-3"><span className="px-2 py-1 rounded text-xs bg-warn/20 text-warn">DEGRADED</span></td>
                <td className="py-3">54.2%</td>
                <td className="py-3">45.0%</td>
              </tr>
            </tbody>
          </table>
          
          {live && risk > 60 && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-crit/10 border border-crit/30 p-4 rounded text-sm text-crit flex items-center justify-between"
            >
              <span>Alert: A17 failure risk critical. Action required.</span>
              <button className="bg-crit text-white px-3 py-1 rounded font-bold">Optimize Plan</button>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
};
