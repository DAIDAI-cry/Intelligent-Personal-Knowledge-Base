import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Check, Copy } from 'lucide-react';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
}

interface CodeBlockProps {
  className?: string;
  children: React.ReactNode;
}

// 独立的代码块组件，避免在回调函数中使用 Hooks
function CodeBlock({ className, children }: CodeBlockProps) {
  const [isCopied, setIsCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const codeContent = String(children).replace(/\n$/, '');

  const handleCopy = () => {
    navigator.clipboard.writeText(codeContent);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  if (match) {
    return (
      <div className="relative group rounded-md my-4 overflow-hidden border border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b border-gray-200">
          <span className="text-xs font-medium text-gray-600">{match[1]}</span>
          <button
            onClick={handleCopy}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            title="Copy code"
          >
            {isCopied ? <Check size={14} className="text-green-600" /> : <Copy size={14} className="text-gray-500" />}
          </button>
        </div>
        <div className="p-4 overflow-x-auto">
          <code className={className}>
            {children}
          </code>
        </div>
      </div>
    );
  }

  return null;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');

          if (!inline && match) {
            return <CodeBlock className={className}>{children}</CodeBlock>;
          }

          return (
            <code className={`${className} bg-gray-200/50 px-1 py-0.5 rounded text-sm font-mono text-pink-600`} {...props}>
              {children}
            </code>
          );
        },
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="mb-1">{children}</li>,
        h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-6 pb-2 border-b border-gray-200">{children}</h1>,
        h2: ({ children }) => <h2 className="text-xl font-bold mb-3 mt-5 pb-1 border-b border-gray-100">{children}</h2>,
        h3: ({ children }) => <h3 className="text-lg font-bold mb-2 mt-4">{children}</h3>,
        h4: ({ children }) => <h4 className="text-base font-bold mb-2 mt-3">{children}</h4>,
        blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4 text-gray-600">{children}</blockquote>,
        a: ({ href, children }) => <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>,
        table: ({ children }) => <div className="overflow-x-auto my-4"><table className="min-w-full divide-y divide-gray-200 border border-gray-200">{children}</table></div>,
        thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
        tbody: ({ children }) => <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>,
        tr: ({ children }) => <tr>{children}</tr>,
        th: ({ children }) => <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 last:border-r-0">{children}</th>,
        td: ({ children }) => <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 border-r border-gray-200 last:border-r-0">{children}</td>,
      }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
