import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { maskKey } from '@/lib/utils';

interface TokenValueDisplayProps {
  value: string;
  label?: string;
  onCopy?: () => void;
}

export const TokenValueDisplay: React.FC<TokenValueDisplayProps> = ({ value, label, onCopy }) => {
  const [showFull, setShowFull] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      onCopy?.();
    } catch {
      // 静默失败
    }
  };

  return (
    <div className="space-y-1.5">
      {label && <span className="text-muted-foreground">{label}</span>}
      <div className="flex gap-2">
        <code className="flex-1 text-xs p-2 rounded bg-muted break-all select-all">
          {showFull ? value : maskKey(value)}
        </code>
        <Button size="sm" variant="outline" onClick={() => setShowFull(!showFull)}>
          {showFull ? '隐藏' : '显示'}
        </Button>
        <Button size="sm" variant="outline" onClick={handleCopy}>
          复制
        </Button>
      </div>
    </div>
  );
};
