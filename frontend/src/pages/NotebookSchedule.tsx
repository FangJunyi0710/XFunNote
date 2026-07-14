import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';

export const NotebookSchedule: React.FC = () => {
  return (
    <NotebookLayout
      notetype="schedule"
      newLabel="添加日程"
      emptyText="暂无日程"
    />
  );
};
