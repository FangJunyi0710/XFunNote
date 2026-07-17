import React from 'react';
import { cn } from '@/lib/utils';

export interface CheckboxProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
  ({ checked = false, onCheckedChange, disabled = false, className, id, ...props }, ref) => {
    return (
      <button
        ref={ref}
        id={id}
        type="button"
        role="checkbox"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onCheckedChange?.(!checked)}
        className={cn(
          'peer h-4 w-4 shrink-0 rounded border border-primary',
          'flex items-center justify-center',
          'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          checked
            ? 'bg-primary text-primary-foreground'
            : 'bg-background',
          className,
        )}
        {...props}
      >
        {checked && (
          <svg
            width="10"
            height="10"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </button>
    );
  },
);
Checkbox.displayName = 'Checkbox';
