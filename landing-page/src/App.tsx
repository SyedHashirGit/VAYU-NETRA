import React from 'react';
import { Nav } from './components/Nav';
import { Hero } from './components/Hero';
import { Problem } from './components/Problem';
import { HowItWorks } from './components/HowItWorks';
import { WhatIfSimulator } from './components/WhatIfSimulator';
import { Features } from './components/Features';
import { DemoTeaser } from './components/DemoTeaser';
import { Footer } from './components/TechStack';

function App() {
  return (
    <div className="min-h-screen text-text-main selection:bg-accent/30">
      <Nav />
      <Hero />
      <Problem />
      <HowItWorks />
      <WhatIfSimulator />
      <Features />
      <DemoTeaser />

      <Footer />
    </div>
  );
}

export default App;
