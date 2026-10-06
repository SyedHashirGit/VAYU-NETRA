import React from 'react';
import { createRoot } from 'react-dom/client';
import { ResponsiveContainer, LineChart, Line, YAxis, XAxis, Tooltip, CartesianGrid } from 'recharts';
import { AircraftViewer } from './components/digital-twin/AircraftViewer';

(window as any).renderSpark = (containerId: string, data: number[], color: string, yLabel: string = '', xLabel: string = 'Time') => {
    const container = document.getElementById(containerId);
    if (!container) return;
    const root = createRoot(container);
    const chartData = data.map((v, i) => ({ val: v, time: `T-${data.length - i}` }));

    root.render(
        <div style={{ width: '100%', height: '160px', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis 
                        dataKey="time" 
                        stroke="var(--mu)" 
                        fontSize={10} 
                        tick={{fill: 'var(--mu)'}} 
                        label={{ value: xLabel, position: 'insideBottom', offset: -15, fill: 'var(--mu)', fontSize: 10 }}
                    />
                    <YAxis 
                        domain={['auto', 'auto']} 
                        stroke="var(--mu)" 
                        fontSize={10} 
                        tick={{fill: 'var(--mu)'}} 
                        label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: 25, fill: 'var(--mu)', fontSize: 10 }}
                    />
                    <Tooltip 
                        contentStyle={{ backgroundColor: 'var(--p2)', border: '1px solid var(--ln)', borderRadius: '4px', fontSize: '11px', color: 'var(--tx)' }}
                        itemStyle={{ color }}
                        labelStyle={{ color: 'var(--mu)' }}
                        formatter={(value: number) => [value.toFixed(2), yLabel]}
                        labelFormatter={(label: string) => `${xLabel}: ${label}`}
                    />
                    <Line type="monotone" dataKey="val" stroke={color} strokeWidth={2} dot={false} isAnimationActive={true} animationDuration={500} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

(window as any).renderDigitalTwin = (containerId: string, aircraftId: string, componentId: string, data: any) => {
    const container = document.getElementById(containerId);
    if (!container) return;
    const root = createRoot(container);
    root.render(<AircraftViewer aircraftId={aircraftId} componentId={componentId} data={data} />);
};
