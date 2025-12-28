import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X } from 'lucide-react';
import hexData from '../hexdata/hexes.json';

interface Hex {
  name: string;
  icon: string;
  effect: string;
  quality: string;
}

const HexesInterface: React.FC = () => {
  const [filter, setFilter] = useState<string>('全部');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const qualities = ['全部', '白银', '黄金', '棱彩'];

  const filteredHexes = useMemo(() => {
    let result = hexData.vectors as Hex[];
    
    // 先按搜索词过滤
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase().trim();
      result = result.filter((hex: Hex) => 
        hex.name.toLowerCase().includes(term) || 
        hex.effect.toLowerCase().includes(term)
      );
    }
    
    // 再按品质过滤
    if (filter === '全部') {
      const qualityOrder: { [key: string]: number } = { '白银': 1, '黄金': 2, '棱彩': 3 };
      return [...result].sort((a: Hex, b: Hex) => {
        return (qualityOrder[a.quality] || 4) - (qualityOrder[b.quality] || 4);
      });
    }
    return result.filter((hex: Hex) => hex.quality === filter);
  }, [filter, searchTerm]);

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case '白银': return 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:shadow-md';
      case '黄金': return 'border-yellow-200 bg-yellow-50/50 text-yellow-900 hover:border-yellow-300 hover:shadow-md';
      case '棱彩': return 'border-fuchsia-200 bg-fuchsia-50/50 text-fuchsia-900 hover:border-fuchsia-300 hover:shadow-md';
      default: return 'border-gray-200 bg-white text-gray-600';
    }
  };

  const getQualityBadgeColor = (quality: string) => {
    switch (quality) {
      case '白银': return 'bg-gray-100 text-gray-600';
      case '黄金': return 'bg-yellow-100 text-yellow-700';
      case '棱彩': return 'bg-fuchsia-100 text-fuchsia-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-white text-gray-900 p-6 overflow-hidden">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
          海克斯科技强化
        </h2>
        <div className="flex items-center gap-4">
          {/* 搜索框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="搜索海克斯名称或效果..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-10 py-2 w-64 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X size={16} />
              </button>
            )}
          </div>
          {/* 品质筛选 */}
          <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg">
            {qualities.map((q) => (
              <button
                key={q}
                onClick={() => setFilter(q)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  filter === q 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200'
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 搜索结果统计 */}
      {searchTerm && (
        <div className="mb-4 text-sm text-gray-500">
          找到 <span className="font-semibold text-blue-600">{filteredHexes.length}</span> 个匹配的海克斯
        </div>
      )}

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {filteredHexes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Search size={48} className="mb-4 opacity-50" />
            <p className="text-lg font-medium">没有找到匹配的海克斯</p>
            <p className="text-sm mt-2">尝试使用其他关键词搜索</p>
          </div>
        ) : (
          <div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
          >
            {filteredHexes.map((hex: Hex, index: number) => (
              <motion.div
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
                key={`${hex.name}-${hex.quality}-${index}`}
                className={`relative group rounded-xl border p-4 cursor-pointer overflow-hidden transition-all duration-300 ${getQualityColor(hex.quality)}`}
              >
                <div className="flex items-center space-x-4 mb-3">
                  <div className="relative w-12 h-12 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0 border border-gray-100">
                    <img 
                      src={hex.icon} 
                      alt={hex.name} 
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://via.placeholder.com/48?text=Hex';
                      }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-lg truncate">{hex.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${getQualityBadgeColor(hex.quality)}`}>
                      {hex.quality}
                    </span>
                  </div>
                </div>
                
                <div className="text-sm opacity-90 leading-relaxed line-clamp-3 group-hover:line-clamp-none transition-all duration-300">
                  {hex.effect}
                </div>

                {/* Hover Glow Effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-black/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HexesInterface;
