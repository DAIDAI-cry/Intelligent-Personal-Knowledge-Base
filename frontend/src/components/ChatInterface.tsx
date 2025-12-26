"use client";

import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  Send, 
  Plus, 
  User, 
  MessageSquare, 
  Trash2, 
  PanelLeftClose, 
  PanelLeftOpen, 
  MoreHorizontal, 
  Pencil, 
  Pin,
  Copy,
  Check,
  LogOut,
  Hexagon,
  Sword,
  Box
} from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { MarkdownRenderer } from "./MarkdownRenderer";
import HexesInterface from "./HexesInterface";
import ItemsInterface from "./ItemsInterface";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: number;
  title: string;
  created_at: string;
  isMarked?: boolean;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState<'chat' | 'hexes' | 'items'>('chat');
  
  // Menu & Rename State
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [newTitle, setNewTitle] = useState("");

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const handleRenameClick = (e: React.MouseEvent, conv: Conversation) => {
    e.stopPropagation();
    setRenamingId(conv.id);
    setNewTitle(conv.title);
    setRenameDialogOpen(true);
    setActiveMenuId(null);
  };

  const handleRenameSubmit = () => {
    if (!renamingId || !newTitle.trim()) return;
    
    setConversations(prev => prev.map(c => 
      c.id === renamingId ? { ...c, title: newTitle.trim() } : c
    ));
    // TODO: Call API to update title on backend
    setRenameDialogOpen(false);
    setRenamingId(null);
    toast.success("重命名成功");
  };

  const handleMarkClick = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setConversations(prev => prev.map(c => 
      c.id === id ? { ...c, isMarked: !c.isMarked } : c
    ));
    setActiveMenuId(null);
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem("accessToken");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get("http://localhost:8000/conversations/", {
        headers: getAuthHeaders(),
      });
      setConversations(response.data);
    } catch (error) {
      console.error("Failed to fetch conversations:", error);
    }
  };

  const loadConversation = async (id: number) => {
    try {
      const response = await axios.get(`http://localhost:8000/conversations/${id}/messages/`, {
        headers: getAuthHeaders(),
      });
      setMessages(response.data);
      setConversationId(id);
    } catch (error) {
      console.error("Failed to load conversation:", error);
      toast.error("无法加载对话历史");
    }
  };

  const deleteConversation = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation(); // 防止触发 loadConversation
    if (!confirm("确定要删除这个对话吗？")) return;

    try {
      await axios.delete(`http://localhost:8000/conversations/${id}/`, {
        headers: getAuthHeaders(),
      });
      
      // 从列表中移除
      setConversations((prev) => prev.filter((c) => c.id !== id));
      
      // 如果删除的是当前选中的对话，重置为新对话
      if (conversationId === id) {
        handleNewChat();
      }
      toast.success("对话已删除");
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      toast.error("删除失败");
    }
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem("accessToken");
      if (token) {
        await axios.post("http://localhost:8000/logout/", {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("username");
      toast.success("已退出登录");
      router.push("/login");
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
  };

  useEffect(() => {
    fetchConversations();
  }, []);

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

    try {
      const response = await axios.post(
        "http://localhost:8000/ask_ai/",
        {
          query: userMessage.content,
          conversation_id: conversationId,
        },
        {
          headers: getAuthHeaders(),
        }
      );

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.data.answer || "抱歉，我没有找到相关信息。",
      };
      setMessages((prev) => [...prev, aiMessage]);
      
      if (!conversationId && response.data.conversation_id) {
        const newId = response.data.conversation_id;
        console.log("New conversation created with ID:", newId); // Debug log
        setConversationId(newId);
        
        // 立即在前端添加新对话到列表顶部
        const newConv: Conversation = {
          id: newId,
          title: userMessage.content.slice(0, 20) + (userMessage.content.length > 20 ? "..." : "") || "新对话",
          created_at: new Date().toISOString(),
        };
        
        // 使用函数式更新确保基于最新状态
        setConversations((prev) => {
            // 防止重复添加
            if (prev.some(c => c.id === newId)) return prev;
            return [newConv, ...prev];
        });
      }
    } catch (error: any) {
      console.error("AI Error:", error);
      toast.error("AI 服务暂时不可用");
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "抱歉，我现在无法连接到大脑，请稍后再试。",
      };
      setMessages((prev) => [...prev, errorMessage]);

      // 即使请求失败，如果后端返回了 conversation_id，我们也应该更新列表
      // Axios 的 error 对象中包含 response
      if (error.response && error.response.data && error.response.data.conversation_id) {
         const newId = error.response.data.conversation_id;
         if (!conversationId) {
            setConversationId(newId);
            const newConv: Conversation = {
                id: newId,
                title: userMessage.content.slice(0, 20) + (userMessage.content.length > 20 ? "..." : "") || "新对话",
                created_at: new Date().toISOString(),
            };
            setConversations((prev) => {
                if (prev.some(c => c.id === newId)) return prev;
                return [newConv, ...prev];
            });
         }
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const renderInputBox = () => (
    <div className="relative flex items-center w-full bg-white border border-gray-300 rounded-full shadow-sm focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-400 transition-all">
      <Button variant="ghost" size="icon" className="ml-2 text-gray-400 hover:text-gray-600 rounded-full">
          <Plus size={20} />
      </Button>
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
        placeholder="给金铲铲智能助手发送消息"
        className="flex-1 border-none shadow-none focus-visible:ring-0 bg-transparent py-4 px-4 text-base h-auto"
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
  );

  return (
    <>
    <div className="flex h-screen bg-white text-gray-900 font-sans">
      {/* Sidebar (Optional, can be hidden on small screens) */}
      <div 
        className={`${isSidebarOpen ? 'w-[260px] border-r' : 'w-0 border-none'} shrink-0 hidden md:flex flex-col bg-gray-50 border-gray-200 transition-all duration-300 ease-in-out overflow-hidden`}
      >
        <div className="w-full flex flex-col h-full">
        <div className="p-4">
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2 text-gray-600 border-gray-300 hover:bg-gray-100"
            onClick={handleNewChat}
          >
            <Plus size={16} />
            新对话
          </Button>
        </div>
        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`group relative px-2 py-2 text-sm rounded-md cursor-pointer grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 w-full ${
                  conversationId === conv.id 
                    ? "bg-gray-200 text-gray-900 font-medium" 
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  {conv.isMarked ? <Pin size={14} className="shrink-0 text-blue-500 fill-blue-500" /> : <MessageSquare size={14} className="shrink-0"/>}
                  <span className="truncate">{conv.title}</span>
                </div>
                
                <button 
                  className={`shrink-0 w-7 h-7 flex items-center justify-center rounded hover:bg-gray-300 transition-colors z-10 ${
                     conversationId === conv.id ? "text-gray-700" : "text-gray-400 hover:text-gray-700"
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMenuId(activeMenuId === conv.id ? null : conv.id);
                  }}
                >
                  <MoreHorizontal size={16} />
                </button>

                {activeMenuId === conv.id && (
                  <>
                    <div 
                        className="fixed inset-0 z-40" 
                        onClick={(e) => { e.stopPropagation(); setActiveMenuId(null); }} 
                    />
                    <div className="absolute right-2 top-8 z-50 w-32 bg-white border border-gray-200 rounded-md shadow-lg py-1 flex flex-col">
                        <button 
                            className="px-3 py-2 text-left text-xs hover:bg-gray-100 flex items-center gap-2"
                            onClick={(e) => handleMarkClick(e, conv.id)}
                        >
                            <Pin size={12} /> {conv.isMarked ? "取消标记" : "标记"}
                        </button>
                        <button 
                            className="px-3 py-2 text-left text-xs hover:bg-gray-100 flex items-center gap-2"
                            onClick={(e) => handleRenameClick(e, conv)}
                        >
                            <Pencil size={12} /> 重命名
                        </button>
                        <button 
                            className="px-3 py-2 text-left text-xs hover:bg-gray-100 text-red-600 flex items-center gap-2"
                            onClick={(e) => {
                                setActiveMenuId(null);
                                deleteConversation(e, conv.id);
                            }}
                        >
                            <Trash2 size={12} /> 删除
                        </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="p-4 border-t border-gray-200">
           <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                  <Avatar className="w-8 h-8 border border-gray-200 bg-gray-100">
                      <AvatarFallback><User size={16}/></AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium text-gray-700 truncate max-w-[120px]">
                      {typeof window !== 'undefined' ? localStorage.getItem("username") || "用户" : "用户"}
                  </span>
              </div>
              <Button 
                  variant="ghost" 
                  size="icon" 
                  className="text-gray-500 hover:text-red-600 hover:bg-red-50"
                  onClick={handleLogout}
                  title="退出登录"
              >
                  <LogOut size={18} />
              </Button>
           </div>
        </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative bg-white min-w-0 overflow-hidden">
        
        {/* Toggle Button (Desktop) - Only show in chat view or if needed */}
        {activeView === 'chat' && (
          <div className="absolute top-3 left-3 z-20 hidden md:block">
              <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="text-gray-500 hover:bg-gray-100"
                  title={isSidebarOpen ? "收起侧边栏" : "展开侧边栏"}
              >
                  {isSidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
              </Button>
          </div>
        )}

        {activeView === 'chat' ? (
          messages.length === 0 ? (
              // === Welcome View ===
              <div className="flex-1 flex flex-col items-center justify-center p-4 w-full">
                  <div className="mb-8 flex items-center gap-3 animate-in fade-in zoom-in duration-500">
                      <img src="/images/jcc_white.png" alt="Logo" className="w-10 h-10 object-contain" />
                      <h2 className="text-2xl font-semibold text-gray-700">今天有什么可以帮到你？</h2>
                  </div>
                  
                  <div className="w-full max-w-2xl px-4 animate-in slide-in-from-bottom-4 duration-700">
                      {renderInputBox()}
                      <div className="text-center mt-4">
                          <p className="text-xs text-gray-400">
                              AI 生成的内容可能不准确，请核对重要信息。
                          </p>
                      </div>
                  </div>
              </div>
          ) : (
              // === Chat View ===
              <div className="flex-1 flex flex-col relative max-w-4xl mx-auto w-full h-full">
                  {/* Header */}
                  <div className="flex items-center p-4 border-b border-gray-100 md:hidden">
                      <span className="font-semibold text-gray-700">金铲铲智能助手</span>
                  </div>

                  {/* Messages */}
                  <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
                  <div className="space-y-6 pb-4">
                      {messages.map((message) => (
                      <MessageBubble key={message.id} message={message} />
                      ))}
                      {isLoading && (
                      <div className="flex gap-4 justify-start">
                          <Avatar className="w-10 h-10 border border-gray-200 bg-white shrink-0 mt-1">
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
                      <div className="max-w-3xl mx-auto">
                          {renderInputBox()}
                          <div className="text-center mt-2">
                              <p className="text-xs text-gray-400">
                                  AI 生成的内容可能不准确，请核对重要信息。
                              </p>
                          </div>
                      </div>
                  </div>
              </div>
          )
        ) : activeView === 'hexes' ? (
           <HexesInterface />
        ) : (
           <ItemsInterface />
        )}
      </div>

      {/* Right Sidebar */}
      <div className="w-[72px] border-l bg-white flex flex-col items-center py-6 gap-4 shrink-0 z-30 shadow-[-1px_0_10px_rgba(0,0,0,0.05)]">
        <NavButton 
          icon={<MessageSquare size={24} />} 
          label="AI问答" 
          isActive={activeView === 'chat'} 
          onClick={() => setActiveView('chat')} 
        />
        <NavButton 
          icon={<Hexagon size={24} />} 
          label="海克斯" 
          isActive={activeView === 'hexes'} 
          onClick={() => setActiveView('hexes')} 
        />
        <NavButton 
          icon={<Box size={24} />} 
          label="装备" 
          isActive={activeView === 'items'} 
          onClick={() => setActiveView('items')} 
        />
      </div>
    </div>

    <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>重命名对话</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="输入新的对话标题"
              onKeyDown={(e) => e.key === "Enter" && handleRenameSubmit()}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameDialogOpen(false)}>取消</Button>
            <Button onClick={handleRenameSubmit}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setIsCopied(true);
    toast.success("已复制");
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div
      className={`flex gap-4 items-start ${
        message.role === "user" ? "justify-end" : "justify-start"
      }`}
    >
      {message.role === "assistant" && (
        <Avatar className="w-10 h-10 border border-gray-200 bg-white shrink-0 mt-1">
          <AvatarImage src="/images/penguin.png" alt="AI" />
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      )}
      
      <div className={`group relative max-w-[80%] ${message.role === "user" ? "text-right" : "text-left"}`}>
        <div
          className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed text-left inline-block ${
            message.role === "user"
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-gray-100 text-gray-800 rounded-bl-sm"
          }`}
        >
          {message.role === "assistant" ? (
             <MarkdownRenderer content={message.content} />
          ) : (
             <div className="whitespace-pre-wrap">{message.content}</div>
          )}
        </div>

        {/* Copy Button */}
        <div className={`absolute top-2 ${message.role === "user" ? "-left-8" : "-right-8"} opacity-0 group-hover:opacity-100 transition-opacity`}>
            <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 rounded-full bg-white hover:bg-gray-100 border border-gray-200 shadow-sm"
                onClick={handleCopy}
                title="复制消息"
            >
                {isCopied ? <Check size={12} className="text-green-600" /> : <Copy size={12} className="text-gray-500" />}
            </Button>
        </div>
      </div>

      {message.role === "user" && (
         <Avatar className="w-10 h-10 border border-gray-200 bg-gray-100 shrink-0 mt-1">
            <AvatarFallback><User size={16}/></AvatarFallback>
         </Avatar>
      )}
    </div>
  );
}


interface NavButtonProps {
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  onClick: () => void;
}

function NavButton({ icon, label, isActive, onClick }: NavButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-all duration-200 group relative ${
        isActive 
          ? "text-blue-600 bg-blue-50" 
          : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"
      }`}
    >
      <div className={`transition-transform duration-200 ${isActive ? "scale-110" : "group-hover:scale-105"}`}>
        {icon}
      </div>
      <span className="text-[10px] font-medium">{label}</span>
      
      {isActive && (
        <motion.div 
          layoutId="activeNavIndicator"
          className="absolute -right-[1px] top-2 bottom-2 w-[3px] bg-blue-600 rounded-l-full"
        />
      )}
    </button>
  );
}
