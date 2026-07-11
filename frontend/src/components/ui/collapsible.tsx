import React from 'react';
import { cn } from '@/lib/utils';

interface CollapsibleContextType {
  open: boolean;
  onToggle: () => void;
}

const CollapsibleContext = React.createContext<CollapsibleContextType>({
  open: false,
  onToggle: () => {},
});

export const Collapsible: React.FC<{
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
}> = ({ open: controlledOpen, onOpenChange, children, className }) => {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const onToggle = () => {
    const next = !open;
    if (onOpenChange) onOpenChange(next);
    else setInternalOpen(next);
  };

  return (
    <CollapsibleContext.Provider value={{ open, onToggle }}>
      <div className={cn(className)}>{children}</div>
    </CollapsibleContext.Provider>
  );
};

export const CollapsibleTrigger: React.FC<{
  children: React.ReactNode;
  className?: string;
  asChild?: boolean;
}> = ({ children, className, asChild }) => {
  const { onToggle } = React.useContext(CollapsibleContext);
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement, {
      onClick: onToggle,
    });
  }
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn('cursor-pointer', className)}
    >
      {children}
    </button>
  );
};

export const CollapsibleContent: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className }) => {
  const { open } = React.useContext(CollapsibleContext);
  if (!open) return null;
  return <div className={cn('animate-fade-in', className)}>{children}</div>;
};
