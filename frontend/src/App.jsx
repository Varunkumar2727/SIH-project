import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';

function App() {
  const [currentView, setCurrentView] = useState('landing');

  return (
    <div className="app-container">
      {currentView === 'landing' ? (
        <Landing onLaunch={() => setCurrentView('dashboard')} />
      ) : (
        <Dashboard />
      )}
    </div>
  );
}

export default App;
