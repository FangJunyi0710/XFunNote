import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { formatDateTime } from '@/lib/utils';
import type { NotebookType } from '@/types/notebook';

interface NotebookDefaultCardListProps {
  type: NotebookType;
  entries: Record<string, any>[];
  displayOrder: string[];
  onEdit: (entry: Record<string, any>) => void;
  onDelete: (id: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  plan: 'border-l-notebook-plan',
  diary: 'border-l-notebook-diary',
  word: 'border-l-notebook-word',
  accumulation: 'border-l-notebook-accumulation',
  aimemory: 'border-l-notebook-aimemory',
  timeline: 'border-l-notebook-timeline',
  schedule: 'border-l-notebook-schedule',
};

/** 核心字段——卡片上不重复显示 */
const CORE_FIELDS = new Set(['id', 'user_id', 'created_at', 'updated_at', 'is_ai_gen', 'ai_tags', 'ai_note']);

export const NotebookDefaultCardList: React.FC<NotebookDefaultCardListProps> = ({
  type,
  entries,
  displayOrder,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="space-y-3">
      {entries.map((entry) => {
        const displayFields = displayOrder.filter(
          (name) => !CORE_FIELDS.has(name) && entry[name] !== null && entry[name] !== undefined && entry[name] !== '',
        );

        return (
          <Card
            key={entry.id}
            className={`border-l-4 ${TYPE_COLORS[type]} transition-shadow hover:shadow-md`}
          >
            <CardContent className="p-4">
              <div className="space-y-1">
                {displayFields.map((field) => (
                  <div key={field} className="flex items-baseline gap-2">
                    <span className="text-xs text-muted-foreground shrink-0">{field}:</span>
                    <span className="text-sm">{String(entry[field])}</span>
                  </div>
                ))}
                {displayFields.length === 0 && (
                  <p className="text-sm text-muted-foreground">(空)</p>
                )}
              </div>
              <div className="flex justify-between items-center mt-2 pt-2 border-t border-border/50">
                <span className="text-[10px] text-muted-foreground">
                  {formatDateTime(entry.created_at)}
                </span>
                <div className="flex gap-1">
                  <button
                    className="text-xs text-primary hover:underline"
                    onClick={() => onEdit(entry)}
                  >
                    编辑
                  </button>
                  <button
                    className="text-xs text-destructive hover:underline"
                    onClick={() => onDelete(entry.id)}
                  >
                    删除
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
