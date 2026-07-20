import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useTokenStore } from '@/stores/tokenStore';
import { exchangeTokenByShortcut, getTokenInfo } from '@/api/tokens';
import { handleError, handleSuccess } from '@/lib/error';
import type { TokenInfo } from '@/api/tokens';
import { Switch } from '@/components/ui/switch';
import { TokenValueDisplay } from '@/components/ui/TokenValueDisplay';
import { DeleteIcon, PlusIcon } from '@/components/ui/icons';
import { maskKey } from '@/lib/utils';
import { Timestamp } from '@/components/ui/Timestamp';

const TOKEN_REGEX = /^sk-[-A-Za-z0-9_]{32}$/;

export const TokenInputPanel: React.FC = () => {
  const {
    users,
    activeUserName,
    addUser,
    removeUser,
    setActiveUser,
    getCurrentUserTokens,
    addToken,
    removeToken,
    setActiveToken,
    getActiveTokenKey,
  } = useTokenStore();

  const [key, setKey] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [exchangeLoading, setExchangeLoading] = useState(false);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);

  const currentTokens = getCurrentUserTokens();
  const activeTokenKey = getActiveTokenKey();
  const activeToken = currentTokens.find((t) => t.key === activeTokenKey);

  useEffect(() => {
    if (activeToken) {
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
  }, [activeToken]);

  const pendingDeleteRef = useRef<string | null>(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [confirmDeleteUserOpen, setConfirmDeleteUserOpen] = useState(false);
  const [pendingDeleteUser, setPendingDeleteUser] = useState<string | null>(null);

  const handleDeleteToken = (id: string) => {
    pendingDeleteRef.current = id;
    setConfirmDeleteOpen(true);
  };

  const executeDeleteToken = () => {
    const id = pendingDeleteRef.current;
    if (id) {
      removeToken(id);
      pendingDeleteRef.current = null;
    }
  };

  const handleDeleteUser = (userName: string) => {
    setPendingDeleteUser(userName);
    setConfirmDeleteUserOpen(true);
  };

  const executeDeleteUser = () => {
    if (pendingDeleteUser) {
      removeUser(pendingDeleteUser);
      setPendingDeleteUser(null);
    }
  };

  const handleSetActiveUser = (userName: string) => {
    setActiveUser(activeUserName === userName ? null : userName);
  };

  const handleAddUser = () => {
    const name = newUserName.trim();
    if (!name) {
      handleError(new Error('用户名不能为空'), '添加用户');
      return;
    }
    if (users[name]) {
      handleError(new Error('用户已存在'), '添加用户');
      return;
    }
    addUser(name);
    setActiveUser(name);
    setNewUserName('');
    handleSuccess('用户已添加');
  };

  const handleAddToken = (tokenKey: string) => {
    const newId = addToken(tokenKey);
    if (newId && !getActiveTokenKey()) {
      setActiveToken(newId);
    }
    return newId;
  };

  const handleSubmitToken = async () => {
    const value = key.trim();
    if (!value) {
      handleError(new Error('Token 值不能为空'), '提交 Token');
      return;
    }
    if (!activeUserName) {
      handleError(new Error('请先选择或创建一个用户'), '提交 Token');
      return;
    }
    if (TOKEN_REGEX.test(value)) {
      handleAddToken(value);
      setKey('');
      handleSuccess('Token 已添加成功');
    } else {
      setExchangeLoading(true);
      try {
        const res = await exchangeTokenByShortcut({ shortcut: value });
        handleAddToken(res.token);
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
      handleSubmitToken();
    }
  };

  const userList = Object.keys(users);

  return (
    <div className="max-w-2xl mx-auto space-y-4 animate-fade-in">
      {/* 用户列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">用户管理</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {userList.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无用户，请添加</p>
          ) : (
            <div className="space-y-1.5">
              {userList.map((name) => (
                <div
                  key={name}
                  className={`flex items-center justify-between px-3 py-2 rounded-md text-sm border transition-colors ${
                    activeUserName === name
                      ? 'border-primary/50 bg-primary/10'
                      : 'border-transparent hover:bg-accent'
                  }`}
                >
                  <span className="font-medium">{name}</span>
                  <div className="flex items-center gap-1">
                    <Switch
                      checked={activeUserName === name}
                      onCheckedChange={() => handleSetActiveUser(name)}
                    />
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteUser(name)}
                      title="删除用户"
                    >
                      <DeleteIcon />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <Input
              placeholder="新用户名"
              value={newUserName}
              onChange={(e) => setNewUserName(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleAddUser} size="sm">
              <PlusIcon />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Token 列表（当前用户） */}
      {activeUserName && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Token 列表（{activeUserName}）</CardTitle>
          </CardHeader>
          <CardContent>
            {currentTokens.length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无 Token，请添加</p>
            ) : (
              <div className="space-y-1.5">
                {currentTokens.map((t) => (
                  <div
                    key={t.id}
                    className={`flex items-center justify-between px-3 py-2 rounded-md text-sm border transition-colors ${
                      activeTokenKey === t.key
                        ? 'border-primary/50 bg-primary/10'
                        : 'border-transparent hover:bg-accent'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-muted-foreground font-mono">{maskKey(t.key)}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 ml-2">
                      <Switch
                        checked={activeTokenKey === t.key}
                        onCheckedChange={(checked) => setActiveToken(checked ? t.id : null)}
                      />
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDeleteToken(t.id)}
                        title="删除 Token"
                      >
                        <DeleteIcon />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 添加新 Token */}
      {activeUserName && (
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
                  onChange={(e) => setKey(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Token / Shortcut"
                  className="flex-1"
                />
                <Button onClick={handleSubmitToken} disabled={!key.trim() || exchangeLoading} size="sm">
                  <PlusIcon />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
                    {tokenInfo.expires_at ? (
                      <Timestamp date={tokenInfo.expires_at} from="year" to="minute" />
                    ) : (
                      '永不过期'
                    )}
                  </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Shortcut 过期：</span>
                  <span className="font-medium">
                    {tokenInfo.shortcut_expire_at ? (
                      <Timestamp date={tokenInfo.shortcut_expire_at} from="year" to="minute" />
                    ) : (
                      '无'
                    )}
                  </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">创建时间：</span>
                  <span className="font-medium">
                    {tokenInfo.created_at ? (
                      <Timestamp date={tokenInfo.created_at} from="year" to="minute" />
                    ) : (
                      <span className="text-red-600">不适用</span>
                    )}
                  </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">更新时间：</span>
                  <span className="font-medium">
                    {tokenInfo.updated_at ? (
                      <Timestamp date={tokenInfo.updated_at} from="year" to="minute" />
                    ) : (
                      <span className="text-red-600">不适用</span>
                    )}
                  </span>
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">状态：</span>
                  <span className={`font-medium ${tokenInfo.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {tokenInfo.is_active ? '已启用' : '已停用'}
                  </span>
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

      <ConfirmDialog
        open={confirmDeleteOpen}
        onOpenChange={setConfirmDeleteOpen}
        title="删除 Token"
        description="确定删除此 Token？此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={executeDeleteToken}
      />

      <ConfirmDialog
        open={confirmDeleteUserOpen}
        onOpenChange={setConfirmDeleteUserOpen}
        title="删除用户"
        description={`确定删除用户“${pendingDeleteUser || ''}”？该用户的所有 Token 将一并删除，此操作不可撤销。`}
        confirmText="删除"
        variant="destructive"
        onConfirm={executeDeleteUser}
      />
    </div>
  );
};
