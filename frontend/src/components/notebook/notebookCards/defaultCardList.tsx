import { NotebookCard } from '@/components/notebook/notebookCards/defaultCard';
import { Pagination } from '@/components/notebook/Pagination';
import type { NotebookType } from '@/config/notebook';

interface DefaultRenderEntryDisplayProps {
  type: NotebookType;
  entries: Record<string, unknown>[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  page?: number;
  pageSize?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

export function defaultRenderEntryDisplay(props: DefaultRenderEntryDisplayProps) {
  const {
    type, entries,
    selectedIds, onToggleSelect,
    page, pageSize, total, onPageChange, onPageSizeChange,
  } = props;

  const isSelectionMode = selectedIds.size > 0;

  return {
    stickySlot: entries.length > 0 && page !== undefined && onPageChange ? (
      <Pagination
        page={page}
        pageSize={pageSize!}
        total={total!}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange!}
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
