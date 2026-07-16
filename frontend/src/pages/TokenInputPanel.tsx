import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTokenStore } from '@/stores/tokenStore';
import { exchangeTokenByShortcut, getTokenInfo } from '@/api/tokens';
import { handleError, handleSuccess } from '@/lib/error';
import type { TokenInfo } from '@/api/tokens';

import { Switch } from '@/components/ui/switch';
import { TokenValueDisplay } from '@/components/ui/TokenValueDisplay';
import { DeleteIcon, PlusIcon } from '@/components/ui/icons';
import { maskKey } from '@/lib/utils';

const TOKEN_REGEX = /^sk-[-A-Za-z0-9_]{32}$/;

export const TokenInputPanel: React.FC = () => {
  const { tokens, activeTokenId, addToken, removeToken, setActiveToken } = useTokenStore();
  const [key, setKey] = useState('');

  const [exchangeLoading, setExchangeLoading] = useState(false);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);

  const activeToken = tokens.find((t) => t.id === activeTokenId);

  useEffect(() => {
    if (activeTokenId) {
      setInfoLoading(true);
      setTokenInfo(null);
      getTokenInfo()
        .then((info) => {
          setTokenInfo(info);
        })
        .catch((e) => {
          handleError(e, '获取 Token 信息失败');
        })
        .finally(() => {
          setInfoLoading(false);
        });
    } else {
      setTokenInfo(null);
    }
  }, [activeTokenId]);

  const handleDelete = (id: string) => {
    if (!confirm('确定删除此 Token？')) return;
    removeToken(id);
  };

  const handleSetActive = (id: string) => {
    setActiveToken(activeTokenId === id ? null : id);
  };

  const handleSubmit = async () => {
    const value = key.trim();
    if (!value) {
      handleError(new Error('Token 值不能为空'), '提交 Token');
      return;
    }
    if (TOKEN_REGEX.test(value)) {
      addToken(value);
      setKey('');
      handleSuccess('Token 已添加成功');
    } else {
      setExchangeLoading(true);
      try {
        const res = await exchangeTokenByShortcut({ shortcut: value });
        addToken(res.token);
        setKey('');
        handleSuccess('Shortcut 兑换成功');
      } catch (e: unknown) {
        handleError(e, '兑换失败');
      } finally {
        setExchangeLoading(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4 animate-fade-in">
      {/* 当前使用的 Token 提示 */}
      {activeToken ? (
        <div className="bg-primary/10 border border-primary/30 text-primary text-sm px-4 py-2.5 rounded-md flex items-center gap-2">
          <span>当前使用：{maskKey(activeToken.key)}</span>
        </div>
      ) : (
        <div className="bg-warning/10 border border-warning/30 text-warning text-sm px-4 py-2.5 rounded-md flex items-center gap-2">
          <span>未选择 Token，API 请求将无法通过鉴权</span>
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
                    <Switch
                      checked={activeTokenId === t.id}
                      onCheckedChange={() => handleSetActive(t.id)}
                    />
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDelete(t.id)}
                      title="删除 Token"
                    >
                      <DeleteIcon/>
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
          <CardTitle className="text-base">
            {key.trim() ? (TOKEN_REGEX.test(key.trim()) ? '添加 Token' : '兑换 Shortcut') : '添加 Token'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="token-key">
              {key.trim() ? (TOKEN_REGEX.test(key.trim()) ? 'Token 值' : 'Shortcut 码') : 'Token 值 / Shortcut 码'}
            </Label>
            <div className="flex gap-2">
              <Input
                id="token-key"
                type="text"
                value={key}
                onChange={(e) => { setKey(e.target.value); }}
                onKeyDown={handleKeyDown}
                placeholder="Token / Shortcut"
                className="flex-1"
              />
              <Button onClick={handleSubmit} disabled={!key.trim() || exchangeLoading} size="sm" title="添加">
                <PlusIcon />
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
            {/* 完整的 Token 值 */}
            <TokenValueDisplay value={activeToken.key} />
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
