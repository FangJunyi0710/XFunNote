import React from 'react';
import { cn } from '@/lib/utils';

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          'flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm',
          'transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {children}
      </select>
    );
  },
);
Select.displayName = 'Select';

export interface SelectItemProps
  extends React.OptionHTMLAttributes<HTMLOptionElement> {}

export const SelectItem = React.forwardRef<HTMLOptionElement, SelectItemProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <option
        ref={ref}
        className={cn('py-1', className)}
        {...props}
      >
        {children}
      </option>
    );
  },
);
SelectItem.displayName = 'SelectItem';

export interface SelectValueProps
  extends React.HTMLAttributes<HTMLSpanElement> {}

export const SelectValue = React.forwardRef<HTMLSpanElement, SelectValueProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn('block truncate', className)}
        {...props}
      >
        {children}
      </span>
    );
  },
);
SelectValue.displayName = 'SelectValue';

export interface SelectTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

export const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm',
          'transition-colors hover:bg-accent hover:text-accent-foreground',
          className,
        )}
        {...props}
      >
        {children}
      </button>
    );
  },
);
SelectTrigger.displayName = 'SelectTrigger';

export interface SelectContentProps
  extends React.HTMLAttributes<HTMLDivElement> {}

export const SelectContent = React.forwardRef<HTMLDivElement, SelectContentProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'relative mt-1 max-h-60 w-full overflow-auto rounded-md border border-input bg-popover text-popover-foreground shadow-md',
          className,
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);
SelectContent.displayName = 'SelectContent';
