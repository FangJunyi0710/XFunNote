import React, { useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { useChatStore } from '@/stores/chatStore';
import { SendIcon } from '@/components/ui/icons';

export const AiChat: React.FC = () => {
  const { messages, loading, sendMessage, clearMessages } =
    useChatStore();
  const [input, setInput] = React.useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput('');
    await sendMessage(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] animate-fade-in">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">AI 对话</h1>
        <Button variant="outline" size="sm" onClick={clearMessages}>
          清空对话
        </Button>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 px-1">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <p className="text-lg mb-2">开始对话</p>
              <p className="text-sm">输入你的问题，AI 助手将为你解答</p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {/* thinking 内容 */}
              {msg.thinking && (
                <details className="mb-2 text-xs opacity-70">
                  <summary className="cursor-pointer font-medium">思考过程</summary>
                  <pre className="mt-1 whitespace-pre-wrap text-xs">
                    {msg.thinking}
                  </pre>
                </details>
              )}
              {/* 主要回复 */}
              <div className="text-sm whitespace-pre-wrap">
                {msg.content || (msg.role === 'assistant' ? (
                  <span className="cursor-blink">▊</span>
                ) : '')}
              </div>
            </div>
          </div>
        ))}

        {/* 加载指示器 */}
        {loading && (
          <div className="flex justify-start">
            <Card className="bg-muted px-4 py-2">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-foreground/40 animate-bounce" />
                <span className="w-1.5 h-1.5 rounded-full bg-foreground/40 animate-bounce [animation-delay:0.1s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-foreground/40 animate-bounce [animation-delay:0.2s]" />
              </div>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div className="flex gap-2 items-end">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          rows={3}
          className="resize-none flex-1"
          disabled={loading}
        />
        <Button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="h-full"
        >
          <SendIcon/>
        </Button>
      </div>
    </div>
  );
};
