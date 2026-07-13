import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Home } from '@/pages/Home';
import { NotebookPlan } from '@/pages/NotebookPlan';
import { NotebookDiary } from '@/pages/NotebookDiary';
import { NotebookWord } from '@/pages/NotebookWord';
import { NotebookAccumulation } from '@/pages/NotebookAccumulation';
import { NotebookAimemory } from '@/pages/NotebookAimemory';
import { AiChat } from '@/pages/AiChat';
import { Management } from '@/pages/Management';
import { TokenInputPanel } from '@/pages/TokenInputPanel';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* 需要鉴权的应用路由 */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="notebooks/plan" element={<NotebookPlan />} />
          <Route path="notebooks/diary" element={<NotebookDiary />} />
          <Route path="notebooks/word" element={<NotebookWord />} />
          <Route path="notebooks/accumulation" element={<NotebookAccumulation />} />
          <Route path="notebooks/aimemory" element={<NotebookAimemory />} />
          <Route path="ai" element={<AiChat />} />
          <Route path="management" element={<Management />} />
          <Route path="token-input" element={<TokenInputPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
