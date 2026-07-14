import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';

export const NotebookAimemory: React.FC = () => {
  return (
    <NotebookLayout
      notetype="aimemory"
      newLabel="添加记忆"
      emptyText="暂无 AI 记忆，AI 会自动管理记忆"
    />
  );
};
