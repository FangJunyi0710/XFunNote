import React, { useCallback, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  autoResize?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, autoResize = false, onChange, ...props }, ref) => {
    const internalRef = useRef<HTMLTextAreaElement | null>(null);

    const setRef = useCallback(
      (node: HTMLTextAreaElement | null) => {
        internalRef.current = node;
        if (typeof ref === 'function') ref(node);
        else if (ref) ref.current = node;
      },
      [ref],
    );

    const resize = useCallback(() => {
      const el = internalRef.current;
      if (!el || !autoResize) return;
      el.style.height = 'auto';
      el.style.height = el.scrollHeight + 'px';
    }, [autoResize]);

    useEffect(() => {
      resize();
    }, [resize, props.value]);

    return (
      <textarea
        ref={setRef}
        className={cn(
          'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm',
          'transition-colors placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          autoResize ? 'resize-none overflow-hidden min-h-[60px]' : 'min-h-[60px]',
          className,
        )}
        onChange={(e) => {
          onChange?.(e);
          resize();
        }}
        {...props}
      />
    );
  },
);
Textarea.displayName = 'Textarea';
