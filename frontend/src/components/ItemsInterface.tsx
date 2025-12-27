import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import equipData from '../hexdata/equip_vectors.json';
import { X, Table, Search } from 'lucide-react';
import { Button } from "@/components/ui/button";

interface Item {
  name: string;
  picture: string;
  basicDesc: string;
  desc: string;
  type: string;
  synthesis?: string;
}

const ItemsInterface: React.FC = () => {
  const [filter, setFilter] = useState<string>('全部');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showSynthesis, setShowSynthesis] = useState(false);
  const [hoveredItem, setHoveredItem] = useState<Item | null>(null);
  const types = ['全部', '基础装备', '成型装备', '光明武器', '辅助装备', '神器装备', '转职纹章', '特殊装备'];

  const basicItemsList = [
    "暴风之剑",
    "反曲之弓",
    "无用大棒",
    "女神之泪",
    "锁子甲",
    "负极斗篷",
    "巨人腰带",
    "拳套",
    "金铲铲",
    "金锅锅"
  ];

  const nameAliases: { [key: string]: string } = {
    "暴风大剑": "暴风之剑"
  };

  const filteredItems = useMemo(() => {
    let result = equipData.vectors as Item[];
    
    // 先按搜索词过滤
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase().trim();
      result = result.filter((item: Item) => 
        item.name.toLowerCase().includes(term) || 
        item.basicDesc?.toLowerCase().includes(term) ||
        item.desc?.toLowerCase().includes(term)
      );
    }
    
    // 再按类型过滤
    if (filter === '全部') {
      const typeOrder: { [key: string]: number } = {
        '基础装备': 1,
        '成型装备': 2,
        '光明武器': 3,
        '辅助装备': 4,
        '神器装备': 5,
        '转职纹章': 6,
        '特殊装备': 7
      };
      return [...result].sort((a: Item, b: Item) => {
        return (typeOrder[a.type] || 8) - (typeOrder[b.type] || 8);
      });
    }
    return result.filter((item: Item) => item.type === filter);
  }, [filter, searchTerm]);

  const synthesisMap = useMemo(() => {
    const map: { [key: string]: { [key: string]: Item } } = {};
    
    // Initialize map for basic items
    basicItemsList.forEach(item1 => {
        map[item1] = {};
        basicItemsList.forEach(item2 => {
            map[item1][item2] = null as any;
        });
    });

    equipData.vectors.forEach((item: Item) => {
      if (item.synthesis) {
        // Format: "ItemA+ItemB=Result"
        const parts = item.synthesis.split('=');
        if (parts.length === 2) {
          const ingredients = parts[0].split('+');
          if (ingredients.length === 2) {
            let item1 = ingredients[0].trim();
            let item2 = ingredients[1].trim();

            // Resolve aliases
            item1 = nameAliases[item1] || item1;
            item2 = nameAliases[item2] || item2;

            if (!map[item1]) map[item1] = {};
            if (!map[item2]) map[item2] = {};

            map[item1][item2] = item;
            map[item2][item1] = item;
          }
        }
      }
    });
    return map;
  }, []);

  const getItemByName = (name: string) => {
    return equipData.vectors.find((i: Item) => i.name === name);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case '基础装备': return 'border-gray-200 bg-gray-50/50 text-gray-900 hover:border-gray-300';
      case '成型装备': return 'border-blue-200 bg-blue-50/50 text-blue-900 hover:border-blue-300';
      case '光明武器': return 'border-yellow-200 bg-yellow-50/50 text-yellow-900 hover:border-yellow-300';
      case '辅助装备': return 'border-green-200 bg-green-50/50 text-green-900 hover:border-green-300';
      case '神器装备': return 'border-orange-200 bg-orange-50/50 text-orange-900 hover:border-orange-300';
      case '转职纹章': return 'border-purple-200 bg-purple-50/50 text-purple-900 hover:border-purple-300';
      case '特殊装备': return 'border-red-200 bg-red-50/50 text-red-900 hover:border-red-300';
      default: return 'border-gray-200 bg-white text-gray-600';
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case '基础装备': return 'bg-gray-100 text-gray-700';
      case '成型装备': return 'bg-blue-100 text-blue-700';
      case '光明武器': return 'bg-yellow-100 text-yellow-700';
      case '辅助装备': return 'bg-green-100 text-green-700';
      case '神器装备': return 'bg-orange-100 text-orange-700';
      case '转职纹章': return 'bg-purple-100 text-purple-700';
      case '特殊装备': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-white text-gray-900 p-6 overflow-hidden relative">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
          装备图鉴
        </h2>
        <div className="flex items-center gap-4">
            {/* 搜索框 */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="搜索装备名称或效果..."
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
            <Button 
                variant="outline" 
                onClick={() => setShowSynthesis(true)}
                className="gap-2"
            >
                <Table size={16} />
                合成表
            </Button>
            <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg overflow-x-auto">
            {types.map((t) => (
                <button
                key={t}
                onClick={() => setFilter(t)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                    filter === t 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200'
                }`}
                >
                {t}
                </button>
            ))}
            </div>
        </div>
      </div>

      {/* 搜索结果统计 */}
      {searchTerm && (
        <div className="mb-4 text-sm text-gray-500">
          找到 <span className="font-semibold text-blue-600">{filteredItems.length}</span> 个匹配的装备
        </div>
      )}

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Search size={48} className="mb-4 opacity-50" />
            <p className="text-lg font-medium">没有找到匹配的装备</p>
            <p className="text-sm mt-2">尝试使用其他关键词搜索</p>
          </div>
        ) : (
          <div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
          >
              {filteredItems.map((item: Item, index: number) => (
                <motion.div
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.2 }}
                  key={`${item.name}-${index}`}
                  className={`relative group rounded-xl border p-4 cursor-pointer overflow-hidden transition-all duration-300 hover:shadow-md ${getTypeColor(item.type)}`}
                >
                  <div className="flex items-center space-x-4 mb-3">
                    <div className="relative w-12 h-12 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0 border border-gray-100">
                      <img 
                        src={item.picture} 
                        alt={item.name} 
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'https://via.placeholder.com/48?text=Item';
                        }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-lg truncate">{item.name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${getTypeBadgeColor(item.type)}`}>
                        {item.type}
                      </span>
                    </div>
                  </div>
                  
                  <div className="text-sm opacity-90 leading-relaxed mb-2">
                      <p className="font-semibold text-xs mb-1 opacity-70">{item.basicDesc}</p>
                      <p className="line-clamp-3 group-hover:line-clamp-none transition-all duration-300">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
          </div>
        )}
      </div>

      {/* Synthesis Table Modal */}
      <AnimatePresence>
        {showSynthesis && (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-50 bg-white/95 backdrop-blur-sm flex flex-col items-center justify-center p-8"
            >
                <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-200 p-6 max-w-full max-h-full overflow-hidden flex gap-6">
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        className="absolute right-4 top-4 z-10"
                        onClick={() => setShowSynthesis(false)}
                    >
                        <X size={24} />
                    </Button>
                    
                    <div className="overflow-auto flex-1">
                        <h3 className="text-2xl font-bold mb-6 text-center">装备合成表</h3>
                        
                        <div className="grid grid-cols-11 gap-1 w-fit mx-auto">
                            {/* Header Row */}
                            <div className="w-12 h-12 p-1 flex items-center justify-center">
                                <img src="/images/jinchanchan.png" alt="Synthesis" className="w-full h-full object-contain opacity-80" />
                            </div>
                            {basicItemsList.map((name) => {
                                const item = getItemByName(name);
                                return (
                                    <div 
                                        key={`header-${name}`} 
                                        className="w-12 h-12 p-1 bg-gray-100 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors" 
                                        title={name}
                                        onMouseEnter={() => item && setHoveredItem(item)}
                                        onMouseLeave={() => setHoveredItem(null)}
                                    >
                                        {item && <img src={item.picture} alt={name} className="w-full h-full object-contain" />}
                                    </div>
                                );
                            })}

                            {/* Rows */}
                            {basicItemsList.map((rowItemName) => {
                                const rowItem = getItemByName(rowItemName);
                                return (
                                    <React.Fragment key={`row-${rowItemName}`}>
                                        {/* Row Header */}
                                        <div 
                                            className="w-12 h-12 p-1 bg-gray-100 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors" 
                                            title={rowItemName}
                                            onMouseEnter={() => rowItem && setHoveredItem(rowItem)}
                                            onMouseLeave={() => setHoveredItem(null)}
                                        >
                                            {rowItem && <img src={rowItem.picture} alt={rowItemName} className="w-full h-full object-contain" />}
                                        </div>
                                        
                                        {/* Cells */}
                                        {basicItemsList.map((colItemName) => {
                                            const resultItem = synthesisMap[rowItemName]?.[colItemName];
                                            return (
                                                <div 
                                                    key={`${rowItemName}-${colItemName}`} 
                                                    className="w-12 h-12 p-1 border border-gray-100 rounded-lg flex items-center justify-center hover:bg-gray-50 transition-colors relative group cursor-pointer"
                                                    title={resultItem ? `${rowItemName} + ${colItemName} = ${resultItem.name}` : '无法合成'}
                                                    onMouseEnter={() => resultItem && setHoveredItem(resultItem)}
                                                    onMouseLeave={() => setHoveredItem(null)}
                                                >
                                                    {resultItem ? (
                                                        <img src={resultItem.picture} alt={resultItem.name} className="w-full h-full object-contain" />
                                                    ) : (
                                                        <span className="text-gray-200 text-xs">-</span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </React.Fragment>
                                );
                            })}
                        </div>
                    </div>

                    {/* Right Side Details Panel */}
                    <div className="w-80 bg-gray-50 rounded-xl p-6 border border-gray-100 flex flex-col shrink-0 overflow-y-auto">
                        {hoveredItem ? (
                            <div className="animate-in fade-in slide-in-from-right-4 duration-200">
                                <div className="w-20 h-20 mx-auto mb-4 bg-white rounded-xl border border-gray-200 p-2 shadow-sm">
                                    <img src={hoveredItem.picture} alt={hoveredItem.name} className="w-full h-full object-contain" />
                                </div>
                                <h4 className="text-xl font-bold text-center mb-2 text-gray-900">{hoveredItem.name}</h4>
                                <div className="flex justify-center mb-6">
                                    <span className={`text-xs font-bold px-3 py-1 rounded-full ${getTypeBadgeColor(hoveredItem.type)}`}>
                                        {hoveredItem.type}
                                    </span>
                                </div>
                                <div className="space-y-6">
                                    {hoveredItem.basicDesc && (
                                        <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
                                            <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">基础属性</h5>
                                            <p className="text-sm font-medium text-gray-900">{hoveredItem.basicDesc}</p>
                                        </div>
                                    )}
                                    {hoveredItem.desc && (
                                        <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
                                            <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">效果</h5>
                                            <p className="text-sm text-gray-700 leading-relaxed">{hoveredItem.desc}</p>
                                        </div>
                                    )}
                                    {hoveredItem.synthesis && (
                                        <div className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm">
                                            <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">合成公式</h5>
                                            <p className="text-sm text-gray-700 font-medium">{hoveredItem.synthesis}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-4">
                                <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
                                    <Table size={32} className="opacity-50" />
                                </div>
                                <p className="text-sm font-medium">鼠标悬停在图标上查看详情</p>
                            </div>
                        )}
                    </div>
                </div>
            </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ItemsInterface;
