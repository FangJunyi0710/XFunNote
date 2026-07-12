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

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="notebooks/plan" element={<NotebookPlan />} />
          <Route path="notebooks/diary" element={<NotebookDiary />} />
          <Route path="notebooks/word" element={<NotebookWord />} />
          <Route path="notebooks/accumulation" element={<NotebookAccumulation />} />
          <Route path="notebooks/aimemory" element={<NotebookAimemory />} />
          <Route path="ai" element={<AiChat />} />
          {/* 视图管理已合并到 /management 的 视图 Tab */}
          <Route path="views" element={<Navigate to="/management" replace />} />
          <Route path="management" element={<Management />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
