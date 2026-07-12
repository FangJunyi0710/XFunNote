import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { DatabaseManagement } from '@/pages/DatabaseManagement';
import { ViewManagement } from '@/pages/ViewManagement';
import { PermissionManagement } from '@/pages/PermissionManagement';
import { TokenManagement } from '@/pages/TokenManagement';

export const Management: React.FC = () => {
  const [tab, setTab] = useState('views');

  return (
    <div className="space-y-4 animate-fade-in">
      <h1 className="text-xl font-bold">⚙️ 系统管理</h1>
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="views">视图</TabsTrigger>
          <TabsTrigger value="permissions">权限</TabsTrigger>
          <TabsTrigger value="tokens">Token</TabsTrigger>
          <TabsTrigger value="database">数据库</TabsTrigger>
        </TabsList>
        <TabsContent value="views">
          <ViewManagement />
        </TabsContent>
        <TabsContent value="permissions">
          <PermissionManagement />
        </TabsContent>
        <TabsContent value="tokens">
          <TokenManagement />
        </TabsContent>
        <TabsContent value="database">
          <DatabaseManagement />
        </TabsContent>
      </Tabs>
    </div>
  );
};
