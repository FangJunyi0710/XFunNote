import React from 'react';
import { Select } from '@/components/ui/select';
import type { ViewFile } from '@/types/view';

interface ViewSelectorProps {
  views: ViewFile[];
  currentView: string | null;
  onSelect: (viewName: string | null) => void;
}

export const ViewSelector: React.FC<ViewSelectorProps> = ({
  views,
  currentView,
  onSelect,
}) => {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">视图:</span>
      <Select
        value={currentView || ''}
        onChange={(e) => onSelect(e.target.value || null)}
        className="w-48"
      >
        <option value="">默认视图</option>
        {views.map((v) => (
          <option key={v.name} value={v.name}>
            {v.name}
          </option>
        ))}
      </Select>
    </div>
  );
};
