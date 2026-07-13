import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTokenStore } from '@/stores/tokenStore';
import { exchangeTokenByShortcut } from '@/api/tokens';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

function maskKey(key: string): string {
  if (key.length <= 8) return key.slice(0, 4) + '****';
  return key.slice(0, 6) + '****' + key.slice(-4);
}

export const TokenInputPanel: React.FC = () => {
  const { tokens, activeTokenId, addToken, removeToken, setActiveToken, updateTokenKey } = useTokenStore();
  const [key, setKey] = useState('');
  const [error, setError] = useState('');

  // 兑换对话框状态
  const [exchangeOpen, setExchangeOpen] = useState(false);
  const [shortcut, setShortcut] = useState('');
  const [exchangeLoading, setExchangeLoading] = useState(false);
  const [exchangeError, setExchangeError] = useState('');

  const activeToken = tokens.find((t) => t.id === activeTokenId);

  const handleAdd = () => {
    const trimmedKey = key.trim();
    if (!trimmedKey) {
      setError('Token 值不能为空');
      return;
    }
    addToken(trimmedKey);
    setKey('');
    setError('');
  };

  const handleDelete = (id: string) => {
    if (!confirm('确定删除此 Token？')) return;
    removeToken(id);
  };

  const handleSetActive = (id: string) => {
    setActiveToken(activeTokenId === id ? null : id);
  };

  const handleExchange = async () => {
    const code = shortcut.trim();
    if (!code) {
      setExchangeError('请输入 Shortcut 码');
      return;
    }
    setExchangeError('');
    setExchangeLoading(true);
    try {
      const res = await exchangeTokenByShortcut({ shortcut: code });
      // 兑换成功：将 token 填入输入框并关闭对话框
      setKey(res.token);
      setExchangeOpen(false);
      setShortcut('');
      setError('');
    } catch (e: any) {
      setExchangeError(e.message || '兑换失败，请检查 Shortcut 码是否有效');
    } finally {
      setExchangeLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4 animate-fade-in">
      {/* 当前使用的 Token 提示 */}
      {activeToken ? (
        <div className="bg-primary/10 border border-primary/30 text-primary text-sm px-4 py-2.5 rounded-md flex items-center gap-2">
          <span>✅ 当前使用：</span>
          <span className="text-xs opacity-70">({maskKey(activeToken.key)})</span>
        </div>
      ) : (
        <div className="bg-warning/10 border border-warning/30 text-warning text-sm px-4 py-2.5 rounded-md flex items-center gap-2">
          <span>⚠️ 未选择 Token，API 请求将无法通过鉴权</span>
        </div>
      )}

      {/* Token 列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">本地 Token 列表</CardTitle>
        </CardHeader>
        <CardContent>
          {tokens.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无 Token，请在下方添加或通过 Shortcut 兑换</p>
          ) : (
            <div className="space-y-1.5">
              {tokens.map((t) => (
                <div
                  key={t.id}
                  className={`flex items-center justify-between px-3 py-2 rounded-md text-sm border transition-colors ${
                    activeTokenId === t.id
                      ? 'border-primary/50 bg-primary/5'
                      : 'border-transparent hover:bg-accent'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {activeTokenId === t.id && (
                        <span className="text-xs text-primary font-medium shrink-0">使用中</span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground font-mono">{maskKey(t.key)}</div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0 ml-2">
                    <Button
                      size="sm"
                      variant={activeTokenId === t.id ? 'default' : 'outline'}
                      onClick={() => handleSetActive(t.id)}
                    >
                      {activeTokenId === t.id ? '取消使用' : '使用'}
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDelete(t.id)}
                    >
                      删除
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 添加新 Token */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">添加 Token</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">
              {error}
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="token-key">Token 值</Label>
            <div className="flex gap-2">
              <Input
                id="token-key"
                type="password"
                value={key}
                onChange={(e) => { setKey(e.target.value); setError(''); }}
                placeholder="粘贴 Token 值"
                className="flex-1"
              />
              <Dialog open={exchangeOpen} onOpenChange={setExchangeOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" type="button">
                    兑换
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Shortcut 兑换</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-2">
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
                    {exchangeError && (
                      <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">
                        {exchangeError}
                      </div>
                    )}
                    <Button
                      className="w-full"
                      onClick={handleExchange}
                      disabled={exchangeLoading || !shortcut.trim()}
                    >
                      {exchangeLoading ? '兑换中...' : '兑换'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
          <Button onClick={handleAdd} disabled={!key.trim()}>
            添加
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
