"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Send, Plus, User } from "lucide-react";
import { motion } from "framer-motion";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "你好！我是金铲铲智能助手。有什么我可以帮你的吗？比如询问当前赛季的强势阵容。",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate AI response (replace with actual API call later)
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "这是一个模拟的回复。在实际应用中，这里将连接到后端 API 获取关于金铲铲之战的智能回答。",
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  return (
    <div className="flex h-[calc(100vh-64px)] bg-white text-gray-900 font-sans">
      {/* Sidebar (Optional, can be hidden on small screens) */}
      <div className="hidden md:flex w-[260px] flex-col bg-gray-50 border-r border-gray-200">
        <div className="p-4">
          <Button variant="outline" className="w-full justify-start gap-2 text-gray-600 border-gray-300 hover:bg-gray-100">
            <Plus size={16} />
            新对话
          </Button>
        </div>
        <ScrollArea className="flex-1 px-2">
          {/* History items would go here */}
          <div className="px-2 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-md cursor-pointer truncate">
            金铲铲强势阵容推荐
          </div>
        </ScrollArea>
        <div className="p-4 border-t border-gray-200">
           {/* User profile or settings */}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center p-4 border-b border-gray-100 md:hidden">
             <span className="font-semibold text-gray-700">金铲铲智能助手</span>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
          <div className="space-y-6 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 items-center ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <Avatar className="w-18 h-18 border border-gray-200 bg-white shrink-0">
                    <AvatarImage src="/images/penguin.png" alt="AI" />
                    {/* <AvatarFallback>AI</AvatarFallback> */}
                  </Avatar>
                )}
                
                <div
                  className={`relative max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    message.role === "user"
                      ? "bg-blue-600 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {message.content}
                </div>

                {message.role === "user" && (
                   <Avatar className="w-18 h-18 border border-gray-200 bg-gray-100 shrink-0">
                      <AvatarFallback><User size={16}/></AvatarFallback>
                   </Avatar>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-4 justify-start">
                 <Avatar className="w-18 h-18 border border-gray-200 bg-white shrink-0">
                    <AvatarImage src="/images/penguin.png" alt="AI" />
                    {/* <AvatarFallback>AI</AvatarFallback> */}
                  </Avatar>
                  <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center">
                    <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 bg-white">
          <div className="relative flex items-center max-w-3xl mx-auto bg-white border border-gray-300 rounded-full shadow-sm focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-400 transition-all">
            <Button variant="ghost" size="icon" className="ml-2 text-gray-400 hover:text-gray-600 rounded-full">
                <Plus size={20} />
            </Button>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="给金铲铲智能助手发送消息"
              className="flex-1 border-none shadow-none focus-visible:ring-0 bg-transparent py-6 px-4 text-base"
            />
            <Button 
                onClick={handleSend} 
                disabled={!input.trim() || isLoading}
                size="icon"
                className={`mr-2 rounded-full transition-all ${input.trim() ? 'bg-black text-white hover:bg-gray-800' : 'bg-gray-200 text-gray-400 hover:bg-gray-200'}`}
            >
              <Send size={18} />
            </Button>
          </div>
          <div className="text-center mt-2">
             <p className="text-xs text-gray-400">
                AI 生成的内容可能不准确，请核对重要信息。
             </p>
          </div>
        </div>
      </div>
    </div>
  );
}
