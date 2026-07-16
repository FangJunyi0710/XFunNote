import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { CopyIcon, EyeIcon, EyeOffIcon } from '@/components/ui/icons';
import { handleSuccess } from '@/lib/error';
import { maskKey } from '@/lib/utils';

interface TokenValueDisplayProps {
  value: string;
}

export const TokenValueDisplay: React.FC<TokenValueDisplayProps> = ({ value }) => {
  const [showFull, setShowFull] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      handleSuccess('Token 已复制到剪贴板');
    } catch {
      // 静默失败
    }
  };

  return (
    <div className="space-y-1.5">
      <span className="text-muted-foreground">Token 值</span>
      <div className="flex gap-2">
        <code className="flex-1 text-xs p-2 rounded bg-muted break-all select-all">
          {showFull ? value : maskKey(value)}
        </code>
        <Button size="sm" variant="outline" onClick={() => setShowFull(!showFull)}>
          {showFull ? <EyeOffIcon /> : <EyeIcon />}
        </Button>
        <Button size="sm" variant="outline" onClick={handleCopy}>
          <CopyIcon />
        </Button>
      </div>
    </div>
  );
};
