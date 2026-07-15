import { NotebookCard } from '@/components/notebook/NotebookCard';
import { Pagination } from '@/components/notebook/Pagination';
import type { NotebookType } from '@/config/notebook';

interface DefaultRenderEntryDisplayProps {
  type: NotebookType;
  entries: Record<string, any>[];
  onEdit: (entry: Record<string, any>) => void;
  onDelete: (id: string) => void;
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
    type, entries, onEdit, onDelete,
    selectedIds, onToggleSelect,
    page, pageSize, total, onPageChange, onPageSizeChange,
  } = props;

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
            key={entry.id}
            type={type}
            entry={entry}
            onEdit={onEdit}
            onDelete={onDelete}
            selected={selectedIds?.has(entry.id) || false}
            onSelect={onToggleSelect}
          />
        ))}
      </div>
    ),
  };
}
