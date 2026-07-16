import { NotebookCard } from '@/components/notebook/notebookCards/defaultCard';
import { Pagination } from '@/components/notebook/Pagination';
import type { NotebookType } from '@/config/notebook';

interface DefaultRenderEntryDisplayProps {
  type: NotebookType;
  entries: Record<string, unknown>[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  offset?: number;
  limit: number;
  total?: number;
  onOffsetChange?: (offset: number) => void;
  onLimitChange: (limit: number) => void;
}

export function defaultRenderEntryDisplay(props: DefaultRenderEntryDisplayProps) {
  const {
    type, entries,
    selectedIds, onToggleSelect,
    offset, limit, total, onOffsetChange, onLimitChange,
  } = props;

  const isSelectionMode = selectedIds.size > 0;

  return {
    stickySlot: entries.length > 0 && offset !== undefined && onOffsetChange ? (
      <Pagination
        offset={offset}
        limit={limit}
        total={total!}
        onOffsetChange={onOffsetChange}
        onLimitChange={onLimitChange}
      />
    ) : undefined,
    content: (
      <div className="space-y-3">
        {entries.map((entry) => (
          <NotebookCard
            key={entry.id as string}
            type={type}
            entry={entry}
            selected={selectedIds?.has(entry.id as string) || false}
            onSelect={onToggleSelect}
            isSelectionMode={isSelectionMode}
          />
        ))}
      </div>
    ),
  };
}
