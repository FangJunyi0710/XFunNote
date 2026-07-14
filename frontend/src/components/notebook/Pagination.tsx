import React, { useState, useCallback } from 'react';
import { Input } from '@/components/ui/input';

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

const ArrowIcon = ({ direction }: { direction: 'left' | 'right' }) => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points={direction === 'left' ? '15 18 9 12 15 6' : '9 6 15 12 9 18'} />
  </svg>
);

const DoubleArrowIcon = ({ direction }: { direction: 'left' | 'right' }) => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {direction === 'left' ? (
      <>
        <polyline points="17 18 11 12 17 6" />
        <polyline points="11 18 5 12 11 6" />
      </>
    ) : (
      <>
        <polyline points="7 6 13 12 7 18" />
        <polyline points="13 6 19 12 13 18" />
      </>
    )}
  </svg>
);

export const Pagination: React.FC<PaginationProps> = ({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  const [inputValue, setInputValue] = useState(String(pageSize));
  const [jumpInputValue, setJumpInputValue] = useState('');

  const handleBlur = useCallback(() => {
    const val = parseInt(inputValue, 10);
    if (!isNaN(val) && val > 0) {
      onPageSizeChange(val);
    } else {
      setInputValue(String(pageSize));
    }
  }, [inputValue, onPageSizeChange, pageSize]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        (e.target as HTMLInputElement).blur();
      }
    },
    [],
  );

  const handleJumpBlur = useCallback(() => {
    const val = parseInt(jumpInputValue, 10);
    if (!isNaN(val) && val >= 1 && val <= totalPages) {
      onPageChange(val);
    }
    setJumpInputValue('');
  }, [jumpInputValue, onPageChange, totalPages]);

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
        <span className="select-none">
          {total > 0 ? `${start}-${end}` : '0'} / {total} 条
        </span>
        <Input
          type="text"
          inputMode="numeric"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value.replace(/\D/g, ''))}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          className="w-16 h-7 text-xs"
        />
        <Input
          type="text"
          inputMode="numeric"
          placeholder="跳转"
          value={jumpInputValue}
          onChange={(e) => setJumpInputValue(e.target.value.replace(/\D/g, ''))}
          onBlur={handleJumpBlur}
          onKeyDown={handleJumpKeyDown}
          className="w-16 h-7 text-xs"
        />
      </div>

      <div className="flex items-center gap-1">
        <button
          className={btnClass}
          disabled={page <= 1}
          onClick={() => onPageChange(1)}
          title="第一页"
        >
          <DoubleArrowIcon direction="left" />
        </button>
        <button
          className={btnClass}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          title="上一页"
        >
          <ArrowIcon direction="left" />
        </button>
        <span className="text-sm text-muted-foreground px-2 select-none">
          {page} / {totalPages}
        </span>
        <button
          className={btnClass}
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          title="下一页"
        >
          <ArrowIcon direction="right" />
        </button>
        <button
          className={btnClass}
          disabled={page >= totalPages}
          onClick={() => onPageChange(totalPages)}
          title="最后一页"
        >
          <DoubleArrowIcon direction="right" />
        </button>
      </div>
    </div>
  );
};
