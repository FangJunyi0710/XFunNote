import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import * as tokensApi from '@/api/tokens';
import * as permissionsApi from '@/api/permissions';
import type { Token } from '@/types/token';
import type { Permission } from '@/types/permission';

const EMPTY_FORM = {
  name: '',
  permission: '',
  is_active: true,
  expires_at: '',
  enable_shortcut: false,
  shortcut: '',
  shortcut_expire_at: '',
};

export const TokenManagement: React.FC = () => {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [createdTokenValue, setCreatedTokenValue] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [tokensRes, permsRes] = await Promise.all([
        tokensApi.listTokens(),
        permissionsApi.listPermissions(),
      ]);
      setTokens(tokensRes || []);
      setPermissions(permsRes || []);
    } catch (e: any) {
      setMessage(`加载失败: ${e.message}`);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const selectToken = async (id: string) => {
    try {
      setLoading(true);
      const t = await tokensApi.getToken(id);
      setSelectedId(t.id);
      setIsCreating(false);
      setCreatedTokenValue(null);
      setForm({
        name: t.name,
        permission: t.permission,
        is_active: t.is_active === 1,
        expires_at: t.expires_at ? t.expires_at.slice(0, 16) : '',
        enable_shortcut: !!t.shortcut,
        shortcut: t.shortcut || '',
        shortcut_expire_at: t.shortcut_expire_at ? t.shortcut_expire_at.slice(0, 16) : '',
      });
      setMessage('');
    } catch (e: any) {
      setMessage(`加载失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNew = () => {
    setSelectedId(null);
    setIsCreating(true);
    setCreatedTokenValue(null);
    setForm({
      name: '',
      permission: permissions.length > 0 ? permissions[0].id : '',
      is_active: true,
      expires_at: '',
      enable_shortcut: false,
      shortcut: '',
      shortcut_expire_at: '',
    });
    setMessage('');
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      setMessage('名称不能为空');
      return;
    }
    if (!form.permission) {
      setMessage('请选择权限');
      return;
    }
    try {
      setLoading(true);
      if (isCreating) {
        const created = await tokensApi.createToken({
          name: form.name.trim(),
          permission: form.permission,
          shortcut: form.enable_shortcut ? form.shortcut || undefined : undefined,
          shortcut_expire_at: form.enable_shortcut && form.shortcut_expire_at ? form.shortcut_expire_at : null,
        });
        setCreatedTokenValue(created.token);
        setMessage('Token 创建成功！请复制并安全保存 token 值。');
        setIsCreating(false);
        setSelectedId(created.id);
      } else if (selectedId) {
        await tokensApi.updateToken(selectedId, {
          name: form.name.trim(),
          permission: form.permission,
          is_active: form.is_active,
          expires_at: form.expires_at || null,
          shortcut: form.enable_shortcut ? (form.shortcut || null) : null,
          shortcut_expire_at: form.enable_shortcut && form.shortcut_expire_at ? form.shortcut_expire_at : null,
        });
        setMessage('保存成功');
      }
      await loadData();
    } catch (e: any) {
      setMessage(`保存失败: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`确定删除此 Token？`)) return;
    try {
      await tokensApi.deleteToken(id);
      if (selectedId === id) {
        setSelectedId(null);
        setIsCreating(false);
        setForm(EMPTY_FORM);
        setCreatedTokenValue(null);
      }
      setMessage('已删除');
      await loadData();
    } catch (e: any) {
      setMessage(`删除失败: ${e.message}`);
    }
  };

  const handleCancel = () => {
    setSelectedId(null);
    setIsCreating(false);
    setForm(EMPTY_FORM);
    setCreatedTokenValue(null);
  };

  const copyToken = async () => {
    if (createdTokenValue) {
      try {
        await navigator.clipboard.writeText(createdTokenValue);
        setMessage('Token 已复制到剪贴板');
      } catch {
        setMessage('复制失败，请手动复制');
      }
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {message && (
        <div className={`text-sm px-3 py-2 rounded flex items-center justify-between ${
          createdTokenValue ? 'bg-warning/10 text-warning border border-warning/30' : 'bg-secondary text-secondary-foreground'
        }`}>
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* 创建成功时显示 token 值 */}
      {createdTokenValue && (
        <Card className="border-warning/30 bg-warning/5">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Token 值（仅显示一次）</span>
              <Button size="sm" variant="outline" onClick={copyToken}>复制</Button>
            </div>
            <code className="block text-xs p-2 rounded bg-warning/10 text-warning break-all select-all">
              {createdTokenValue}
            </code>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Token 列表 */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Token 列表</CardTitle>
            <Button size="sm" onClick={handleNew}>新建</Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {tokens.length === 0 && (
                <p className="text-xs text-muted-foreground">暂无 Token</p>
              )}
              {tokens.map((t) => (
                <div
                  key={t.id}
                  className={`flex items-center justify-between px-2 py-1.5 rounded cursor-pointer text-sm hover:bg-accent ${
                    selectedId === t.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => selectToken(t.id)}
                >
                  <div className="truncate flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium truncate">{t.name}</span>
                      <Badge variant={t.is_active ? 'success' : 'secondary'} className="shrink-0">
                        {t.is_active ? '启用' : '禁用'}
                      </Badge>
                      {t.shortcut && (
                        <Badge variant="outline" className="shrink-0 text-[10px]">
                          Shortcut
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {t.permission}
                      {t.expires_at && ` | 过期: ${new Date(t.expires_at).toLocaleDateString()}`}
                      {t.shortcut && ` | 短码: ${t.shortcut}`}
                    </div>
                  </div>
                  <button
                    className="text-xs text-destructive hover:underline shrink-0 ml-2"
                    onClick={(e) => { e.stopPropagation(); handleDelete(t.id); }}
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 编辑表单 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">
              {isCreating ? '新建 Token' : selectedId ? `编辑: ${form.name}` : '选择 Token'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(isCreating || selectedId) ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="tname">名称</Label>
                    <Input
                      id="tname"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="Token 名称"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="tperm">权限</Label>
                    <Select
                      id="tperm"
                      value={form.permission}
                      onChange={(e) => setForm({ ...form, permission: e.target.value })}
                    >
                      {permissions.length === 0 && (
                        <option value="">暂无权限，请先创建</option>
                      )}
                      {permissions.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.id})
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>启用</Label>
                    <div className="flex items-center gap-2 pt-1">
                      <Switch
                        checked={form.is_active}
                        onCheckedChange={(v) => setForm({ ...form, is_active: v })}
                      />
                      <span className="text-sm text-muted-foreground">
                        {form.is_active ? '已启用' : '已禁用'}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="texp">过期时间</Label>
                    <Input
                      id="texp"
                      type="datetime-local"
                      value={form.expires_at}
                      onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                    />
                    <p className="text-xs text-muted-foreground">留空表示永不过期</p>
                  </div>
                </div>

                {/* Shortcut 兑换码配置 */}
                <div className="space-y-3 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <Label className="font-medium">Shortcut 兑换码</Label>
                    <Switch
                      checked={form.enable_shortcut}
                      onCheckedChange={(v) => setForm({ ...form, enable_shortcut: v })}
                    />
                  </div>
                  {form.enable_shortcut && (
                    <div className="grid grid-cols-2 gap-4 pl-2 border-l-2 border-primary/30">
                      <div className="space-y-1.5">
                        <Label htmlFor="tshortcut">自定义短码</Label>
                        <Input
                          id="tshortcut"
                          value={form.shortcut}
                          onChange={(e) => setForm({ ...form, shortcut: e.target.value })}
                          placeholder="留空则自动生成"
                        />
                        <p className="text-xs text-muted-foreground">留空由系统自动生成唯一短码</p>
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="tshortcut_exp">短码过期时间</Label>
                        <Input
                          id="tshortcut_exp"
                          type="datetime-local"
                          value={form.shortcut_expire_at}
                          onChange={(e) => setForm({ ...form, shortcut_expire_at: e.target.value })}
                        />
                        <p className="text-xs text-muted-foreground">留空表示与 Token 一致</p>
                      </div>
                    </div>
                  )}
                </div>

                {!isCreating && selectedId && (() => {
                  const t = tokens.find((tk) => tk.id === selectedId);
                  return t ? (
                    <div className="space-y-2">
                      <div className="space-y-1.5">
                        <Label>Token 值（只读）</Label>
                        <div className="flex gap-2">
                          <code className="flex-1 text-xs p-2 rounded bg-muted break-all select-all">
                            {t.token}
                          </code>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={async () => {
                              try {
                                await navigator.clipboard.writeText(t.token);
                                setMessage('Token 已复制到剪贴板');
                              } catch {
                                setMessage('复制失败');
                              }
                            }}
                          >
                            复制
                          </Button>
                        </div>
                      </div>
                      {t.shortcut && (
                        <div className="space-y-1">
                          <Label>Shortcut 兑换码</Label>
                          <div className="flex items-center gap-2">
                            <code className="text-xs p-2 rounded bg-muted font-mono">
                              {t.shortcut}
                            </code>
                            {t.shortcut_expire_at && (
                              <span className="text-xs text-muted-foreground">
                                过期: {new Date(t.shortcut_expire_at).toLocaleString()}
                              </span>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                try {
                                  await navigator.clipboard.writeText(t.shortcut!);
                                  setMessage('Shortcut 已复制到剪贴板');
                                } catch {
                                  setMessage('复制失败');
                                }
                              }}
                            >
                              复制短码
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : null;
                })()}

                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={handleCancel}>取消</Button>
                  <Button onClick={handleSave} disabled={loading}>
                    {loading ? '保存中...' : '保存'}
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                从左侧选择一个 Token，或点击"新建"创建
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
