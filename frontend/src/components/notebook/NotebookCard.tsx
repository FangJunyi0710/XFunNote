import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDateTime } from '@/lib/utils';
import type { NotebookType } from '@/types/notebook';

interface NotebookCardProps {
  type: NotebookType;
  entry: Record<string, any>;
  selected?: boolean;
  onSelect?: (id: string) => void;
  onEdit?: (entry: Record<string, any>) => void;
  onDelete?: (id: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  plan: 'border-l-notebook-plan',
  diary: 'border-l-notebook-diary',
  word: 'border-l-notebook-word',
  accumulation: 'border-l-notebook-accumulation',
  aimemory: 'border-l-notebook-aimemory',
};

const TYPE_LABELS: Record<NotebookType, string> = {
  plan: '计划',
  diary: '日记',
  word: '单词',
  accumulation: '积累',
  aimemory: 'AI 记忆',
};

export const NotebookCard: React.FC<NotebookCardProps> = ({
  type,
  entry,
  selected,
  onSelect,
  onEdit,
  onDelete,
}) => {
  const renderContent = () => {
    switch (type) {
      case 'plan':
        return (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              {entry.no && <span className="text-xs font-mono text-muted-foreground">{entry.no}</span>}
              <span className="text-xs text-muted-foreground">{entry.month}</span>
              <span className="font-medium">{entry.content?.split('\n')[0] || '(无标题)'}</span>
              {entry.done ? (
                <Badge variant="success" className="text-[10px]">已完成</Badge>
              ) : (
                <Badge variant="secondary" className="text-[10px]">进行中</Badge>
              )}
              {entry.status && (
                <Badge variant="outline" className="text-[10px]">{entry.status}</Badge>
              )}
            </div>
            {entry.content && (
              <p className="text-sm text-muted-foreground line-clamp-2">
                {entry.content.split('\n').slice(1).join('\n') || entry.content}
              </p>
            )}
          </div>
        );

      case 'diary':
        return (
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">{entry.date}</div>
            {(entry.mood || entry.weather) && (
              <div className="text-xs text-muted-foreground">
                {entry.mood && `心情: ${entry.mood}`}
                {entry.mood && entry.weather && ' · '}
                {entry.weather && `天气: ${entry.weather}`}
              </div>
            )}
            <p className="text-sm line-clamp-3">{entry.content || '(空)'}</p>
          </div>
        );

      case 'word':
        return (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-base">{entry.word}</span>
              {entry.phonetic && (
                <span className="text-sm text-muted-foreground">/{entry.phonetic}/</span>
              )}
              {entry.part_of_speech && (
                <span className="text-xs text-muted-foreground">({entry.part_of_speech})</span>
              )}
            </div>
            {entry.example && (
              <p className="text-xs text-muted-foreground line-clamp-1 italic">"{entry.example}"</p>
            )}
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <span>复习 {entry.review_count ?? 0} 次</span>
              <span>掌握度 {((entry.performance ?? 0) * 100).toFixed(0)}%</span>
              {entry.next_review && <span>下次: {entry.next_review}</span>}
            </div>
            {entry.related_words && (
              <p className="text-xs text-muted-foreground">关联: {entry.related_words}</p>
            )}
          </div>
        );

      case 'accumulation':
        return (
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground line-clamp-2">{entry.content}</p>
            {entry.source && (
              <p className="text-xs text-muted-foreground">来源: {entry.source}</p>
            )}
            {entry.note && (
              <p className="text-xs text-muted-foreground">备注: {entry.note}</p>
            )}
          </div>
        );

      case 'aimemory':
        return (
          <div className="space-y-1">
            <span className="font-medium">{entry.title || '(无标题)'}</span>
            <p className="text-sm text-muted-foreground line-clamp-2">{entry.content}</p>
            {entry.source && (
              <p className="text-xs text-muted-foreground">来源: {entry.source}</p>
            )}
          </div>
        );

      default:
        return <pre className="text-xs">{JSON.stringify(entry, null, 2)}</pre>;
    }
  };

  return (
    <Card
      className={`border-l-4 ${TYPE_COLORS[type]} cursor-pointer transition-shadow hover:shadow-md ${
        selected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={() => onSelect?.(entry.id)}
    >
      <CardContent className="p-4">
        {renderContent()}
        <div className="flex justify-between items-center mt-2 pt-2 border-t border-border/50">
          <span className="text-[10px] text-muted-foreground">
            {formatDateTime(entry.created_at)}
          </span>
          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
            <button
              className="text-xs text-primary hover:underline"
              onClick={() => onEdit?.(entry)}
            >
              编辑
            </button>
            <button
              className="text-xs text-destructive hover:underline"
              onClick={() => onDelete?.(entry.id)}
            >
              删除
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
