import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { exchangeTokenByShortcut } from '@/api/tokens';

export const TokenShortcutExchange: React.FC = () => {
  const [shortcut, setShortcut] = useState('');
  const [result, setResult] = useState<{ token: string; name: string; permission: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleExchange = async () => {
    const code = shortcut.trim();
    if (!code) {
      setError('请输入 Shortcut 码');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await exchangeTokenByShortcut({ shortcut: code });
      setResult(res);
    } catch (e: any) {
      setError(e.message || '兑换失败，请检查 Shortcut 码是否有效');
    } finally {
      setLoading(false);
    }
  };

  const copyToken = async () => {
    if (result) {
      try {
        await navigator.clipboard.writeText(result.token);
        setError('');
      } catch {
        setError('复制失败，请手动复制');
      }
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-4 animate-fade-in">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">🔑 Token Shortcut 兑换</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            输入管理员提供的 Shortcut 码，兑换完整的 Token 值。
          </p>

          <div className="space-y-1.5">
            <Label htmlFor="shortcut-input">Shortcut 码</Label>
            <Input
              id="shortcut-input"
              value={shortcut}
              onChange={(e) => setShortcut(e.target.value)}
              placeholder="请输入 Shortcut 码"
              onKeyDown={(e) => { if (e.key === 'Enter') handleExchange(); }}
            />
          </div>

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">
              {error}
            </div>
          )}

          <Button
            className="w-full"
            onClick={handleExchange}
            disabled={loading || !shortcut.trim()}
          >
            {loading ? '兑换中...' : '兑换'}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-base text-primary">兑换成功</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm">
              <span className="text-muted-foreground">名称：</span>
              <span className="font-medium">{result.name}</span>
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">权限：</span>
              <span className="font-medium">{result.permission}</span>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">Token 值（仅显示一次）</span>
                <Button size="sm" variant="outline" onClick={copyToken}>复制</Button>
              </div>
              <code className="block text-xs p-2 rounded bg-primary/10 text-primary break-all select-all">
                {result.token}
              </code>
            </div>
            <p className="text-xs text-muted-foreground">
              请立即复制并安全保存此 Token 值，关闭页面后将无法再次查看。
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
