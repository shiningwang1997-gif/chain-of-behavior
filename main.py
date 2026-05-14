import argparse
import importlib
import os
import sys

# 让 Python 能找到 tasks/
sys.path.append(os.path.dirname(__file__))

# --------------------------
# 动态加载 run / run_standard / extract_expressions / verify
# --------------------------
def dynamic_import(task_folder: str, mode: str):
    """
    动态导入 tasks/{task_folder}/{mode}.py 的 main() 函数
    mode 可以是 run / run_standard / extract_expressions / verify
    """
    module_name = mode
    module_path = f"tasks.{task_folder}.{module_name}"
    try:
        module = importlib.import_module(module_path)
        return module.main
    except Exception as e:
        raise ImportError(f"❌ Failed to import {module_path}: {e}")

# --------------------------
# 主函数
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="Chain-of-Behavior Project Launcher")
    parser.add_argument(
        "--task",
        type=str,
        default="g24",
        choices=["g24", "sliding", "sudoku"],
        help="Choose which task to run."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="run",
        choices=["run", "run_standard", "extract_expressions", "verify"],
        help="Choose which mode to execute."
    )
    args = parser.parse_args()

    task_folder = args.task
    mode = args.mode

    print(f"\n🚀 Starting task: {task_folder} with mode: {mode}\n")

    # 1️⃣ 执行主要任务（run / run_standard / extract_expressions / verify）
    func = dynamic_import(task_folder, mode)
    func()

    # 2️⃣ 如果是 extract_expressions 模式，自动做表达式验证
    if mode == "extract_expressions":
        print("\n🔍 Running verification after extraction...\n")
        try:
            verify_func = dynamic_import(task_folder, "verify_expressions")
            verify_func()
        except ImportError:
            print("⚠️ verify_expressions.py not found. Skipping.")

    print(f"\n🎉 Task {task_folder} finished.\n")


if __name__ == "__main__":
    main()
