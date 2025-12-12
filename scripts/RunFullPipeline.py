import subprocess
import sys
import time
from pathlib import Path

# --- 路径配置 ---
# 当前脚本位于 scripts/ 目录下
CURRENT_DIR = Path(__file__).parent

# 子脚本位于 scripts/Chunk-Embed-Upsert/ 目录下
SUB_SCRIPT_DIR = CURRENT_DIR / "Chunk-Embed-Upsert"

# 定义三个子脚本的绝对路径
SCRIPT_CHUNK = SUB_SCRIPT_DIR / "ChunkedItemsScript.py"
SCRIPT_EMBED = SUB_SCRIPT_DIR / "EmbedItemsScript.py"
SCRIPT_UPSERT = SUB_SCRIPT_DIR / "UpsertItemsScript.py"

def run_step(script_path, step_name):
    """
    运行单个 Python 脚本并检查结果
    """
    # 检查脚本文件是否存在
    if not script_path.exists():
        print(f"\n{'!'*20} 错误: 找不到脚本文件 {'!'*20}")
        print(f"路径: {script_path}")
        sys.exit(1)

    print(f"\n{'='*20} 正在执行步骤: {step_name} {'='*20}")
    print(f"脚本路径: {script_path.name}")
    
    start_time = time.time()
    
    try:
        # 使用当前运行环境的 Python 解释器执行子脚本
        # check=True 表示如果脚本返回非 0 状态码（报错），会抛出异常
        # capture_output=False 让子脚本的打印内容直接显示在当前终端
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True
        )
        
        elapsed = time.time() - start_time
        print(f"{'='*20} 步骤完成: {step_name} (耗时 {elapsed:.2f}s) {'='*20}\n")
        
    except subprocess.CalledProcessError as e:
        print(f"\n{'!'*20} 步骤失败: {step_name} {'!'*20}")
        print(f"退出代码: {e.returncode}")
        print("流水线已终止，请检查上述错误信息。")
        sys.exit(1) # 终止整个流程
    except KeyboardInterrupt:
        print("\n用户手动中断。")
        sys.exit(1)
    except Exception as e:
        print(f"\n{'!'*20} 发生未知错误: {step_name} {'!'*20}")
        print(f"错误信息: {e}")
        sys.exit(1)

def main():
    print(f"启动全量数据处理流水线...")
    print(f"工作目录: {CURRENT_DIR}")
    
    # 1. Chunking (切分)
    # 将 OriginData -> ChunkedData
    run_step(SCRIPT_CHUNK, "1. 数据切分 (Chunking)")
    
    # 2. Embedding (向量化)
    # 将 ChunkedData -> EmbeddedData (调用 Pinecone Inference)
    run_step(SCRIPT_EMBED, "2. 向量生成 (Embedding)")
    
    # 3. Upsert (上传)
    # 将 EmbeddedData -> Pinecone Database
    run_step(SCRIPT_UPSERT, "3. 存入数据库 (Upsert)")
    
    print("\n" + "#"*60)
    print(" 恭喜！全流程执行完毕，数据已成功存入 Pinecone。")

if __name__ == "__main__":
    main()
