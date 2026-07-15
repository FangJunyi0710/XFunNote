import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTokenStore } from '@/stores/tokenStore';
import { exchangeTokenByShortcut, getTokenInfo } from '@/api/tokens';
import type { TokenInfo } from '@/api/tokens';

import { TokenValueDisplay } from '@/components/ui/TokenValueDisplay';
import { maskKey } from '@/lib/utils';

export const TokenInputPanel: React.FC = () => {
  const { tokens, activeTokenId, addToken, removeToken, setActiveToken } = useTokenStore();
  const [key, setKey] = useState('');
  const [error, setError] = useState('');

  // 兑换状态（内联，无对话框）

  const [exchangeLoading, setExchangeLoading] = useState(false);
  const [exchangeError, setExchangeError] = useState('');
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoError, setInfoError] = useState('');

  const activeToken = tokens.find((t) => t.id === activeTokenId);

  useEffect(() => {
    if (activeTokenId) {
      setInfoLoading(true);
      setInfoError('');
      setTokenInfo(null);
      getTokenInfo()
        .then((info) => {
          setTokenInfo(info);
        })
        .catch((e) => {
          setInfoError(e.message || '获取 Token 信息失败');
        })
        .finally(() => {
          setInfoLoading(false);
        });
    } else {
      setTokenInfo(null);
      setInfoError('');
    }
  }, [activeTokenId]);

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
    const code = key.trim();
    if (!code) {
      setExchangeError('请输入 Shortcut 码');
      return;
    }
    setExchangeError('');
    setExchangeLoading(true);
    try {
      const res = await exchangeTokenByShortcut({ shortcut: code });
      // 兑换成功：自动添加到列表，但不自动激活
      addToken(res.token);
      setKey('');
      setError('');
      setExchangeError('');
    } catch (e: unknown) {
      setExchangeError(e instanceof Error ? e.message : '兑换失败，请检查 Shortcut 码是否有效');
    } finally {
      setExchangeLoading(false);
    }
  };

  const displayError = error || exchangeError;

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
          {displayError && (
            <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">
              {displayError}
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="token-key">Token 值 / Shortcut 码</Label>
            <div className="flex gap-2">
              <Input
                id="token-key"
                type="text"
                value={key}
                onChange={(e) => { setKey(e.target.value); setError(''); setExchangeError(''); }}
                placeholder="粘贴 Token 值或输入 Shortcut 码"
                className="flex-1"
              />
              <Button variant="outline" type="button" onClick={handleExchange} disabled={exchangeLoading || !key.trim()}>
                {exchangeLoading ? '兑换中...' : '兑换'}
              </Button>
              <Button onClick={handleAdd} disabled={!key.trim()}>
                添加
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Token 详细信息（选中时显示） */}
      {activeToken && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">当前 Token 详细信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {infoLoading && (
              <div className="text-sm text-muted-foreground px-3 py-2">加载 Token 信息中...</div>
            )}
            {infoError && (
              <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">
                {infoError}
              </div>
            )}
            {tokenInfo && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-muted-foreground">名称：</span>
                    <span className="font-medium">{tokenInfo.name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Shortcut：</span>
                    <span className="font-medium">{tokenInfo.shortcut || '无'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">过期时间：</span>
                    <span className="font-medium">
                      {tokenInfo.expires_at
                        ? new Date(tokenInfo.expires_at).toLocaleString()
                        : '永不过期'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Shortcut 过期：</span>
                    <span className="font-medium">
                      {tokenInfo.shortcut_expire_at
                        ? new Date(tokenInfo.shortcut_expire_at).toLocaleString()
                        : '无'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">创建时间：</span>
                    <span className="font-medium">
                      {new Date(tokenInfo.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">更新时间：</span>
                    <span className="font-medium">
                      {new Date(tokenInfo.updated_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                {/* 完整的 Token 值 */}
                <TokenValueDisplay value={activeToken.key} label="完整 Token 值" />
                {tokenInfo.read_view && (
                  <div>
                    <span className="text-muted-foreground">读权限视图：</span>
                    <code className="block mt-1 text-xs p-2 rounded bg-muted break-all">
                      {JSON.stringify(tokenInfo.read_view, null, 2)}
                    </code>
                  </div>
                )}
                {tokenInfo.write_view && (
                  <div>
                    <span className="text-muted-foreground">写权限视图：</span>
                    <code className="block mt-1 text-xs p-2 rounded bg-muted break-all">
                      {JSON.stringify(tokenInfo.write_view, null, 2)}
                    </code>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
