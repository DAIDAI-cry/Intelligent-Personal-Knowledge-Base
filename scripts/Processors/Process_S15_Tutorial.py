import sys
from pathlib import Path

# --- 路径设置：确保能导入 utils ---
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

from scripts.utils.BasePineconeProcessor import BasePineconeProcessor

class S15TutorialProcessor(BasePineconeProcessor):
    def load_text(self):
        """
        重写加载逻辑：
        使用包含详细元数据的高质量语义分块数据。
        """
        self.chunks = [
            {
                "category": "游戏介绍",
                "title": "S15赛季新手入坑指南",
                "description": "介绍S15赛季更新背景，适合新手入坑的时机以及竞技游戏的基本过程。",
                "tags": ["S15", "新手", "入坑"],
                "content": "2025年S15赛季刚刚更新，是新手正式入坑的好时机。本教程将手把手教你成为金铲铲大佬，详细介绍竞技游戏的过程。"
            },
            {
                "category": "奇遇机制",
                "title": "S15赛季奇遇机制详解",
                "description": "解释每局游戏开始时的随机奇遇机制及其对游戏可玩性的影响。",
                "tags": ["奇遇", "机制", "随机"],
                "content": "每局游戏刚开始会出现一个随机的“奇遇”机制。有的奇遇功能十分强大，增加了游戏的可玩性。"
            },
            {
                "category": "游戏流程",
                "title": "游戏阶段与野怪回合",
                "description": "详解游戏的八个大阶段划分，以及1阶段野怪回合的掉落机制。",
                "tags": ["阶段", "野怪", "法球"],
                "content": "整个游戏最多有八个大阶段，每个阶段包含好几个回合，通常用“大阶段-回合”（如1-2）表示。第一个大阶段（1-2, 1-3, 1-4）是对战野怪。野怪会掉落蓝色和白色的法球，点击屏幕控制小小英雄捡起，可获得最高三费的棋子或装备散件。"
            },
            {
                "category": "棋子属性",
                "title": "棋子面板与属性介绍",
                "description": "如何查看棋子的星级、费用、羁绊、血量蓝量以及技能定位。",
                "tags": ["棋子", "属性", "星级", "费用"],
                "content": "点击棋子，右侧方框显示详细信息：1. 星级：三张一星棋子合成一张二星，以此类推，最高三星。2. 价值（费用）：数字后加“费”表示，通常最高为五费。3. 羁绊：即棋子的职业或种族。4. 属性：绿条为血量，蓝条为蓝量。蓝量满后释放技能。5. 技能与定位：点击图标查看具体介绍和推荐站位。"
            },
            {
                "category": "装备系统",
                "title": "装备合成与推荐",
                "description": "散件与成装的区别，如何合成装备以及查看棋子推荐装备。",
                "tags": ["装备", "合成", "散件"],
                "content": "打野怪获得的装备称为“散件”，加成较小。将两个散件结合可以合成为“成装”，加成较大。点击右下角设计旁的按键可查看合成表。点击棋子可查看该棋子的推荐装备。"
            },
            {
                "category": "羁绊系统",
                "title": "羁绊激活与查看",
                "description": "羁绊系统的基本概念，如何激活羁绊以及查看羁绊详细信息。",
                "tags": ["羁绊", "激活", "职业"],
                "content": "屏幕左侧显示羁绊信息。当几个拥有相同羁绊的不同棋子同时上场并达到一定数量，便可激活此羁绊。点击羁绊图标可查看详细内容及拥有此羁绊的棋子。"
            },
            {
                "category": "等级系统",
                "title": "人口等级与经验机制",
                "description": "等级对棋子数量的影响，经验值的获取方式及购买规则。",
                "tags": ["等级", "经验", "人口"],
                "content": "屏幕左下角显示等级，等级代表棋盘上可上场的棋子数量。每回合结束免费获得2点经验值。也可以花费4个金币购买4点经验值来升级。"
            },
            {
                "category": "经济系统",
                "title": "金币获取与利息规则",
                "description": "详解金币的来源（固定、利息、连胜连败）以及利息的计算方式。",
                "tags": ["金币", "利息", "经济"],
                "content": "金币来源主要有两处：1. 固定与额外收入：每回合结束有固定金币，连胜或连败会有额外奖励。2. 利息：每存10金币，下回合结束获得1金币利息，以此类推，通常最高5金币利息（即存50块）。金币用于购买经验或刷新商店购买棋子。"
            },
            {
                "category": "商店系统",
                "title": "商店购买与刷新概率",
                "description": "如何在商店购买棋子，刷新商店，锁定棋子以及不同等级的卡牌刷新概率。",
                "tags": ["商店", "刷新", "概率"],
                "content": "点击金币图标进入商店购买棋子。花费2金币可刷新商店。可以使用“锁定按钮”定住商店棋子不刷新。商店下方显示各费用卡牌的刷新概率：等级越高，高费卡概率越高，低费卡概率降低。"
            },
            {
                "category": "强化符文",
                "title": "海克斯强化符文选择",
                "description": "海克斯出现的阶段、品质分类以及对战局和阵容选择的影响。",
                "tags": ["海克斯", "符文", "阵容"],
                "content": "在2-1、3-2、4-2阶段会有强化符文（俗称海克斯）选择。分为银色、金色、彩色三种品质。每次有三次刷新机会。好的海克斯可以改变战局，通常根据海克斯来选择阵容。"
            },
            {
                "category": "选秀环节",
                "title": "选秀机制与操作",
                "description": "选秀回合的时间点、选择顺序规则以及操作技巧。",
                "tags": ["选秀", "装备", "抢牌"],
                "content": "每个阶段的第四回合会有一次选秀。选择顺序按照玩家血量从低到高排列。选秀可以提前获取高费棋子或关键装备。可以通过点击查看属性，或设置摇杆控制移动。"
            }
        ]

    def clean_text(self, text):
        """针对该视频特定的 OCR 错误修正"""
        replacements = {
            "一菲": "一费",
            "一负四十": "1-4时",
            "一杠二": "1-2",
            "一杠三": "1-3",
            "二杠四": "2-4",
            "二杠一": "2-1",
            "三杠二": "3-2",
            "四杠二": "4-2",
            "新宿": "羁绊",
            "新秀": "新手",
            "成交": "成装",
            "细锁": "锁定按钮",
            "移到": "一到",
            "无非": "五费",
            "机子": "棋子",
            "键位": "站位",
            "一键成交": "一件成装"
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def get_category(self, text):
        return "通用教程"

if __name__ == "__main__":
    # 输出路径指向 datas/OriginData
    output_file = PROJECT_ROOT / "datas" / "OriginData" / "s15_tutorial_pinecone.json"
    
    processor = S15TutorialProcessor(
        input_path="", 
        output_path=str(output_file),
        source_name="s15_tutorial",
        doc_type="tutorial", # 明确指定 type 为 tutorial
        version="S15"
    )
    processor.process()
