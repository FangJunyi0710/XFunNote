import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Home } from '@/pages/Home';
import { NotebookFilter } from '@/pages/NotebookFilter';
import { NotebookEditPage } from '@/pages/NotebookEditPage';

import { AiChat } from '@/pages/AiChat';
import { Management } from '@/pages/Management';
import { TokenInputPanel } from '@/pages/TokenInputPanel';

import { NOTEBOOK_ROUTES, NOTEBOOK_PAGES } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';

const App: React.FC = () => {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        {/* 需要鉴权的应用路由 */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          {Object.entries(NOTEBOOK_ROUTES).map(([key, route]) => {
            const PageComponent = NOTEBOOK_PAGES[key as NotebookType];
            return (
              <Route
                key={key}
                path={route.path.replace(/^\//, '')}
                element={<PageComponent />}
              />
            );
          })}
          <Route path="notebooks/:notetype/new" element={<NotebookEditPage />} />
          <Route path="notebooks/:notetype/edit/:id" element={<NotebookEditPage />} />
          <Route path="notebooks/:notetype/batch-update" element={<NotebookEditPage />} />
          <Route path="notebooks/:notetype/filter" element={<NotebookFilter />} />
          <Route path="ai" element={<AiChat />} />
          <Route path="management" element={<Management />} />
          <Route path="token-input" element={<TokenInputPanel />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
