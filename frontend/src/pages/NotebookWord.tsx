import React from 'react';
import { NotebookLayout } from '@/components/notebook/NotebookLayout';

export const NotebookWord: React.FC = () => {
  return (
    <NotebookLayout
      notetype="word"
      newLabel="添加单词"
      emptyText='暂无单词，点击"添加单词"开始'
    />
  );
};
