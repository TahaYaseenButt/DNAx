import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopNavBar from './components/TopNavBar';
import HomePage from './pages/HomePage';
import SizeCalcPage from './pages/SizeCalcPage';
import DNAGeneratePage from './pages/DNAGeneratePage';
import ComparatorPage from './pages/ComparatorPage';
import PrimerPage from './pages/PrimerPage';
import QPCRPage from './pages/QPCRPage';
import ExportPage from './pages/ExportPage';
import MatrixDBPage from './pages/MatrixDBPage';
import ProtocolPage from './pages/ProtocolPage';
import { api } from './api';

export default function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [history, setHistory] = useState(['home']);
  const [forwardStack, setForwardStack] = useState([]);
  const [collapsed, setCollapsed] = useState(false);
  const [dbCount, setDbCount] = useState(0);

  // Shared state across the pipeline
  const [targetBp, setTargetBp] = useState(500);
  const [constructData, setConstructData] = useState(null);

  const refreshDbCount = async () => {
    try {
      const seqs = await api.getSequences();
      setDbCount(seqs?.length || 0);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refreshDbCount();
  }, [currentPage]);

  const navigateTo = (newPage) => {
    if (newPage === currentPage) return;
    setHistory((prev) => [...prev, newPage]);
    setForwardStack([]);
    setCurrentPage(newPage);
  };

  const handleGoBack = () => {
    if (history.length <= 1) return;
    const newHist = [...history];
    const popped = newHist.pop();
    const prevPage = newHist[newHist.length - 1];

    setHistory(newHist);
    setForwardStack((prev) => [popped, ...prev]);
    setCurrentPage(prevPage);
  };

  const handleGoForward = () => {
    if (forwardStack.length === 0) return;
    const newFwd = [...forwardStack];
    const nextPage = newFwd.shift();

    setForwardStack(newFwd);
    setHistory((prev) => [...prev, nextPage]);
    setCurrentPage(nextPage);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage setCurrentPage={navigateTo} dbCount={dbCount} lastConstruct={constructData} />;
      case 'size':
        return <SizeCalcPage setCurrentPage={navigateTo} setTargetBp={setTargetBp} />;
      case 'dna':
        return (
          <DNAGeneratePage
            setCurrentPage={navigateTo}
            targetBp={targetBp}
            setConstructData={setConstructData}
            constructData={constructData}
          />
        );
      case 'comparator':
        return <ComparatorPage setCurrentPage={navigateTo} constructData={constructData} />;
      case 'primer':
        return <PrimerPage setCurrentPage={navigateTo} constructData={constructData} />;
      case 'qpcr':
        return <QPCRPage setCurrentPage={navigateTo} constructData={constructData} />;
      case 'export':
        return (
          <ExportPage
            setCurrentPage={navigateTo}
            constructData={constructData}
            refreshDbCount={refreshDbCount}
          />
        );
      case 'matrix_db':
        return <MatrixDBPage setCurrentPage={navigateTo} />;
      case 'protocol':
        return <ProtocolPage />;
      default:
        return <HomePage setCurrentPage={navigateTo} dbCount={dbCount} />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans relative">
      {/* --- Ambient Multi-Color Gradient Mesh Layer (Provides Authentic Glass Refraction) --- */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Sky / Cyan Orb */}
        <div className="ambient-glow-1 absolute -top-24 left-1/4 w-[650px] h-[650px] bg-gradient-to-br from-sky-300/35 to-cyan-400/25 rounded-full blur-[110px]" />
        
        {/* Indigo / Purple Orb */}
        <div className="ambient-glow-2 absolute top-1/3 -right-24 w-[700px] h-[700px] bg-gradient-to-br from-indigo-300/30 to-purple-400/25 rounded-full blur-[130px]" />
        
        {/* Emerald / Teal Orb */}
        <div className="ambient-glow-3 absolute -bottom-28 left-1/3 w-[600px] h-[600px] bg-gradient-to-br from-emerald-200/30 to-teal-300/20 rounded-full blur-[120px]" />
        
        {/* Rose / Violet Orb */}
        <div className="ambient-glow-1 absolute top-2/3 -left-20 w-[500px] h-[500px] bg-gradient-to-br from-rose-200/25 to-violet-300/20 rounded-full blur-[110px]" />
      </div>

      {/* 1. Left Vertical Frosted Glass Sidebar */}
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={navigateTo}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
      />

      {/* 2. Right Main Layout */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative z-10">
        {/* Frosted Top Header */}
        <TopNavBar
          currentPage={currentPage}
          setCurrentPage={navigateTo}
          canGoBack={history.length > 1}
          canGoForward={forwardStack.length > 0}
          onGoBack={handleGoBack}
          onGoForward={handleGoForward}
          dbCount={dbCount}
        />

        {/* Scrollable Glass Viewport */}
        <main className="flex-1 overflow-y-auto relative">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}
