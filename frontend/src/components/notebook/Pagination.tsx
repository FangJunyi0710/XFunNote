import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { ArrowIcon, DoubleArrowIcon } from '@/components/ui/icons';

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onOffsetChange: (offset: number) => void;
  onLimitChange: (limit: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  offset,
  limit,
  total,
  onOffsetChange,
  onLimitChange,
}) => {
  const totalPages = Math.max(1, Math.ceil((total - offset) / limit) + Math.ceil(offset / limit));
  const currentPage = Math.max(1, Math.ceil(offset / limit) + 1);
  const start = Math.max(offset + 1, 1);
  const end = Math.min(offset + limit, total);
  const [inputValue, setInputValue] = useState('');
  const [jumpInputValue, setJumpInputValue] = useState('');
  const [showPageSizeInput, setShowPageSizeInput] = useState(false);
  const [showJumpInput, setShowJumpInput] = useState(false);
  const pageSizeInputRef = useRef<HTMLInputElement>(null);
  const jumpInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showPageSizeInput && pageSizeInputRef.current) {
      pageSizeInputRef.current.focus();
    }
  }, [showPageSizeInput]);

  useEffect(() => {
    if (showJumpInput && jumpInputRef.current) {
      jumpInputRef.current.focus();
    }
  }, [showJumpInput]);

  const handleBlur = useCallback(() => {
    const val = parseInt(inputValue, 10);
    if (!isNaN(val) && val > 0) {
      onLimitChange(val);
    }
    setInputValue('');
    setShowPageSizeInput(false);
  }, [inputValue, onLimitChange]);

  const goToPage = useCallback((page: number) => {
    const clampedPage = Math.min(page, totalPages);
    onOffsetChange(offset + limit * (clampedPage - currentPage));
  }, [offset, limit, totalPages, currentPage, onOffsetChange]);

  const handleJumpBlur = useCallback(() => {
    const val = parseInt(jumpInputValue, 10);
    if (!isNaN(val) && val >= 1 && val <= total) {
      onOffsetChange(val - 1);
    }
    setJumpInputValue('');
    setShowJumpInput(false);
  }, [jumpInputValue, onOffsetChange, total]);

  const handleJumpKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        (e.target as HTMLInputElement).blur();
      }
    },
    [],
  );

  const btnClass =
    'h-7 w-7 flex items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors disabled:pointer-events-none disabled:opacity-50';

  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {showPageSizeInput ? (
          <Input
            ref={pageSizeInputRef}
            type="text"
            inputMode="numeric"
            placeholder="每页条数"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.replace(/\D/g, ''))}
            onBlur={handleBlur}
            onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
            className="max-w-20 h-7 text-xs"
          />
        ) : (
          <span
            className="select-none whitespace-nowrap cursor-pointer"
            onClick={() => setShowPageSizeInput(true)}
          >
            {total > 0 ? `${start}-${end}` : '0'} / {total}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1">
        <button
          className={btnClass}
          disabled={currentPage <= 1}
          onClick={() => goToPage(1)}
          title="第一页"
        >
          <DoubleArrowIcon direction="left" />
        </button>
        <button
          className={btnClass}
          disabled={currentPage <= 1}
          onClick={() => goToPage(currentPage - 1)}
          title="上一页"
        >
          <ArrowIcon direction="left" />
        </button>
        {showJumpInput ? (
          <Input
            ref={jumpInputRef}
            type="text"
            inputMode="numeric"
            placeholder="跳转条目"
            value={jumpInputValue}
            onChange={(e) => setJumpInputValue(e.target.value.replace(/\D/g, ''))}
            onBlur={handleJumpBlur}
            onKeyDown={handleJumpKeyDown}
            className="max-w-20 h-7 text-xs"
          />
        ) : (
          <span
            className="text-sm text-muted-foreground px-2 select-none whitespace-nowrap cursor-pointer"
            onClick={() => setShowJumpInput(true)}
          >
            {currentPage} / {totalPages}
          </span>
        )}
        <button
          className={btnClass}
          disabled={currentPage >= totalPages}
          onClick={() => goToPage(currentPage + 1)}
          title="下一页"
        >
          <ArrowIcon direction="right" />
        </button>
        <button
          className={btnClass}
          disabled={currentPage >= totalPages}
          onClick={() => goToPage(totalPages)}
          title="最后一页"
        >
          <DoubleArrowIcon direction="right" />
        </button>
      </div>
    </div>
  );
};
