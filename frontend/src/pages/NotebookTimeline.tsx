import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';

export const NotebookTimeline: React.FC = () => {
  return (
    <NotebookLayout
      notetype="timeline"
      newLabel="添加事件"
      emptyText="暂无时间线事件"
    />
  );
};
