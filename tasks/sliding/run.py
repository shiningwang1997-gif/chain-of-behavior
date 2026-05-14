import csv
import os
import json
import ast
import re
from copy import deepcopy
from prompts.sliding.template import EXECUTE_WORKFLOW_TEMPLATE
from model.deepseek_client import call_llm_with_prompt
global deep_index
deep_index = 0
# ---------- 配置与常量 ----------
DATA_FILE = "data/sliding/sliding.json"
OUTPUT_FILE = "output/sliding/solutions.jsonl"

GOAL_STATE = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 0]
]

# ---------- 基础辅助函数 ----------
def print_board(board):
    print("-------")
    for row in board:
        # 0 显示为空格，更直观
        print("| " + " ".join(str(n) if n != 0 else " " for n in row) + " |")
    print("-------")

def find_zero(board):
    """找到空位(0)的坐标"""
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return r, c
    return None

def get_move_type_code(llm_output_str):
    """
    解析 LLM 输出，返回移动类型的状态码。
    
    Returns:
        1: 顺时针旋转 (Rotate CW)
        2: 逆时针旋转 (Rotate CCW)
        0: 其他情况 (普通移动、解析失败、非旋转操作)
    """
    move_data = None

    # --- 步骤 1: 尝试解析 JSON ---
    try:
        # 使用正则寻找最外层的 {}，防止字符串包含额外空格或说明
        json_match = re.search(r'\{.*\}', llm_output_str.strip(), re.DOTALL)
        if json_match:
            move_data = json.loads(json_match.group())
        else:
            # 没找到 JSON，说明是简单移动 (Option 1)
            return 0
    except Exception:
        # JSON 格式错误，视为无效或简单移动
        return 0

    # --- 步骤 2: 多重条件判断 ---
    
    # 必须是字典，且类型显式标记为 'rotate' 或者是隐式旋转 (含有 rectangle 字段)
    if isinstance(move_data, dict) and (move_data.get("type") == "rotate" or "rectangle" in move_data):
        
        direction = move_data.get("direction")
        
        if direction == "CW":
            return 1  # 顺时针
        elif direction == "CCW":
            return 2  # 逆时针
            
    # 如果不满足上述旋转条件，或者 direction 写错了，都归为 0
    return 0

def is_number_at_position(board, number, position):
    """
    判断 board 中指定坐标位置的数字是否等于目标数字。
    
    参数:
    board: list[list[int]] - 二维数组棋盘
    number: int - 要验证的数字
    position: tuple or list - 坐标 (row_index, col_index)
    
    返回:
    bool - 如果位置合法且数字匹配返回 True，否则返回 False
    """
    try:
        r, c = position
        
        # 1. 边界检查 (防止 Index Error)
        # 检查行号是否有效
        if not (0 <= r < len(board)):
            return False
        # 检查列号是否有效 (假设每行长度一致)
        if not (0 <= c < len(board[0])):
            return False
            
        # 2. 核心判断
        return board[r][c] == number
        
    except (TypeError, ValueError, IndexError):
        # 如果输入的 position 格式不对（比如传了None或长度不够），直接返回 False
        return False
    
def is_number_in_row(board, number, row_index):
    """
    判断数字是否位于指定的行中。
    利用 is_number_at_position 进行原子判断，确保边界安全。
    
    参数:
    board: list[list[int]] - 二维数组棋盘
    number: int - 要查找的数字
    row_index: int - 目标行号 (0-based)
    
    返回:
    bool - 如果该行包含该数字返回 True，否则返回 False
    """
    # 1. 基础防卫：如果棋盘为空
    if not board:
        return False
        
    # 获取列数
    cols_count = len(board[0])
    
    # 2. 遍历该行的每一列
    for c in range(cols_count):
        # 构建坐标 (行, 列) 并调用已有的健壮函数
        if is_number_at_position(board, number, (row_index, c)):
            return True
            
    return False

def is_number_in_col(board, number, col_index):
    """
    判断数字是否位于指定的列中。
    利用 is_number_at_position 进行原子判断，确保边界安全。
    
    参数:
    board: list[list[int]] - 二维数组棋盘
    number: int - 要查找的数字
    col_index: int - 目标列号 (0-based)
    
    返回:
    bool - 如果该列包含该数字返回 True，否则返回 False
    """
    # 1. 基础防卫
    if not board:
        return False
        
    # 获取行数
    rows_count = len(board)
    
    # 2. 遍历每一行，检查固定的 col_index
    for r in range(rows_count):
        # 构建坐标 (当前行, 目标列) 并调用健壮函数
        # 注意这里变动的是行号 r，列号 col_index 是固定的
        if is_number_at_position(board, number, (r, col_index)):
            return True
            
    return False
    
def is_one_inside_zero_rectangle(board):
    """
    判断数字 1 是否位于由 [数字 0 的位置] 和 [固定点 (0, 1)] 构成的矩形区域内。
    
    参数:
    board: 3x3 的二维列表
    
    返回:
    bool: 如果 1 在矩形内返回 True，否则 False
    """
    # 1. 寻找 0 和 1 的坐标
    pos_0 = None
    rows = len(board)
    cols = len(board[0])
    
    for r in range(rows):
        for c in range(cols):
            val = board[r][c]
            if val == 0:
                pos_0 = (r, c)
    
    # 安全检查：防止棋盘数据错误找不到 0 或 1
    if pos_0 is None:
        return False

    # 2. 定义矩形边界
    # 矩形的一个顶点是 0 的位置 (r0, c0)
    # 另一个顶点是固定点 (0, 1)
    fixed_r, fixed_c = 0, 1
    r0, c0 = pos_0
    
    # 确定矩形的行范围 [min_r, max_r] 和 列范围 [min_c, max_c]
    min_r = min(r0, fixed_r)
    max_r = max(r0, fixed_r)
    
    min_c = min(c0, fixed_c)
    max_c = max(c0, fixed_c)
    
    is_in_row = min_r <= 0 <= max_r
    is_in_col = min_c <= 0 <= max_c
    
    return is_in_row and is_in_col

def are_numbers_adjacent(board, num1, num2):
    """
    判断两个数字在棋盘上是否相邻（上下或左右，不含对角线）。
    
    原理：
    计算两个坐标的曼哈顿距离：|r1-r2| + |c1-c2|
    如果等于 1，说明是相邻；
    如果等于 0，说明是同一个位置；
    如果大于 1，说明不相邻或是对角线（对角线距离为2）。
    
    参数:
    board: list[list[int]] - 二维棋盘
    num1, num2: int - 要判断的两个数字
    
    返回:
    bool - 相邻返回 True，否则 False
    """
    pos1 = None
    pos2 = None
    
    # 1. 遍历棋盘找到两个数字的坐标
    rows = len(board)
    cols = len(board[0])
    
    for r in range(rows):
        for c in range(cols):
            val = board[r][c]
            if val == num1:
                pos1 = (r, c)
            elif val == num2:
                pos2 = (r, c)
    
    # 2. 安全检查：如果有数字不在棋盘上，自然不相邻
    if pos1 is None or pos2 is None:
        return False
        
    # 3. 计算曼哈顿距离
    r1, c1 = pos1
    r2, c2 = pos2
    
    distance = abs(r1 - r2) + abs(c1 - c2)
    
    return distance == 1

def choose_case(board, CW_bool):
    # 1. 优先处理旋转逻辑 (卫语句)
    if CW_bool == 1: return 'CW'
    if CW_bool == 2: return 'CCW'

    # 2. 顺序检查数字位置 (展平逻辑)
    # 逻辑：只要有一个没对齐，就确定是该阶段的 case，并跳出检查
    if not is_number_at_position(board, 1, (0, 0)):
        case_type = 'case00'
    elif not is_number_at_position(board, 2, (0, 1)):
        case_type = 'case01'
    elif not is_number_at_position(board, 3, (0, 2)):
        case_type = 'case02'
    elif not is_number_at_position(board, 4, (1, 0)):
        case_type = 'case10'
    elif not is_number_at_position(board, 7, (2, 0)):
        case_type = 'case20'
    elif not (is_number_at_position(board, 5, (1, 1)) and is_number_at_position(board, 6, (1, 2)) and is_number_at_position(board, 8, (2, 1))):
        case_type = 'case111221'
    else:
        return None

    # 3. 获取并格式化步骤
    step = choose_step(board, case_type)
    
    # 简单的一步移动直接返回，否则拼接 case_type
    if step in ["U", "L", "D", "R"]:
        return step
    else:
        return f"{case_type}/{step}"

def choose_step(board, case_type):
    if deep_index == 0:
        if case_type == 'case00':
            if is_number_at_position(board, 0, (1,1)) and is_number_at_position(board, 1, (2,2)):
                step = 'UDLR'
            else:
                step = 'core'
        elif case_type == 'case01':
            if (is_number_at_position(board, 0, (1,0)) or is_number_at_position(board, 0, (2,0))) and is_number_at_position(board, 2, (0,2)):
                step = 'R'
            elif is_one_inside_zero_rectangle(board)==False:
                step = 'core'
            elif is_number_in_row(board, 0, 0) and (is_number_at_position(board, 2, (1,0)) or is_number_at_position(board, 2, (2,0))):
                step = "D"
            else:
                step = "sub"
        elif case_type == 'case02':
            if is_number_at_position(board, 0, (1,0)):
                step = 'R'
            elif (is_number_at_position(board, 3, (1,0)) or is_number_in_row(board, 3, 2)) and (is_number_at_position(board, 0, (0,2)) or is_number_at_position(board, 0, (1,1)) or is_number_at_position(board, 0, (1,1))):
                step = 'core'
                deep_index = 'case02core'
            elif is_number_at_position(board, 0, (0,2)) and is_number_at_position(board, 3, (1,1)):
                step = 'D'
            elif is_number_at_position(board, 0, (0,2)) and is_number_at_position(board, 3, (1,2)):
                step = 'D'
                deep_index = 'case02D'
            else:
                step = 'sub'
        elif case_type == 'case10':
            step = 'core'
        elif case_type == 'case20':
            if (is_number_at_position(board, 7, (1,2)) or is_number_at_position(board, 7, (2,2))) and (is_number_at_position(board, 0, (2,0)) or is_number_at_position(board, 0, (1,1)) or is_number_at_position(board, 0, (2,1))):
                step = 'core'
                deep_index = 'case20core'
            elif is_number_at_position(board, 7, (1,1)) or is_number_at_position(board, 0, (2,0)):
                step = 'R'
            elif is_number_at_position(board, 7, (2,1)) or is_number_at_position(board, 0, (2,0)):
                step = 'U'
                deep_index = 'case20U'
            else:
                step = 'sub'
        elif case_type == 'case111221':
            if are_numbers_adjacent(board, 5, 6):
                step = '56'
                deep_index = 'case11122156'
            else:
                step = '58'
                deep_index = 'case11122158'

    elif deep_index == 'case02D':
        if is_number_at_position(board, 0, (0,1)):
            step = 'D'
        else:
            step = 'next_core'
            deep_index = 'case02next_core'

    elif deep_index == 'case02core':
        if is_number_in_row(board, 0, 0):
            step = 'D'
        else:
            if is_number_at_position(board, 0, (0,1)):
                step = 'D'
            else:
                step = 'next_core'
                deep_index = 'case02next_core'

    elif deep_index == 'case02next_core':
        if is_number_in_col(board, 0, 0):
            step = 'R'
        else:
            step = 'next_next_core'
            deep_index = 0

    elif deep_index == 'case20core' or deep_index == 'case20U':
        if is_number_in_col(board, 0, 0) or is_number_at_position(board, 0, (1,0)):
            step = 'R'
        else:
            step = 'next_core'
            deep_index = 'case20next_core'

    elif deep_index == 'case20next_core':
        step = 'next_next_core'
        deep_index = 0

    elif deep_index == 'case11122156':
        step = 'R'
        deep_index = 0

    elif deep_index == 'case11122158':
        step = 'D'
        deep_index = 0

    return step

def execute_step(board,CW_bool):
    step_type = choose_case(board, CW_bool)
    workflow_file = os.path.join("prompts", "sliding", f"{step_type}.txt")
    with open(workflow_file, "r") as f:
        workflow_text = f.read()
    
    output_instruction = (
    "Answer: show all reasoning steps for the next move.\n"
    "Identify the coordinates of the empty space (0), list valid adjacent neighbors (Up, Down, Left, Right), and explain why the chosen move brings the board closer to the GOAL_STATE.\n"
    "⚠ While generating the next state, ensure that you ONLY swap the empty space (0) with an adjacent number.\n"
    "⚠ IMPORTANT: You MUST strictly follow the physics of the 8-puzzle:\n"
    "  - Diagonal moves are STRICTLY FORBIDDEN.\n"
    "  - You cannot move a tile into a non-empty space. You can only 'slide' into 0.\n"
    "  - The set of numbers {0, 1, ..., 8} must remain invariant; do not duplicate or lose any digits.\n"
    "Do NOT predict multiple steps ahead; output only the immediate next single state.\n"
    "Do NOT output the board in any non-Python format.\n"
    "Use Python list format (e.g., [[1,2,3],...]) for the output board."
    )

    prompt = EXECUTE_WORKFLOW_TEMPLATE.format(
        input=board,
        output=output_instruction,
        step_type=step_type,
        workflow=workflow_text
    )

    print(f"Requesting Reasoning...")
    reasoning_result = call_llm_with_prompt(prompt)
    print(f"Agent Reasoning: {reasoning_result[:200]}...") # 打印部分推理，防止刷屏

    extraction_prompt = (
        "Extract the resulting board state and the move decision from the reasoning above into a single line.\n"
        "Format the output strictly as: BOARD_STATE;MOVE_DECISION\n"
        "(Use a semicolon ';' to separate the board and the move)\n\n"
        "Part 1: BOARD_STATE\n"
        "- A Python list of lists representing the 3x3 grid. Example: [[1, 2, 3], [4, 5, 6], [7, 8, 0]]\n"
        "- Must contain exactly digits 0-8 with no duplicates.\n"
        "- Do NOT use quotes around the list.\n\n"
        "Part 2: MOVE_DECISION\n"
        "- Option A (Slide): A single character 'U', 'D', 'L', or 'R'.\n"
        "- Option B (Rotation): A valid JSON string. Example: {\"type\": \"rotate\", \"direction\": \"CW\", ...}\n\n"
        "STRICT RULES:\n"
        "1. Output exactly one line.\n"
        "2. Do NOT use Markdown, code blocks, or explanations.\n"
        "3. Ensure the delimiter between board and move is a semicolon ';'.\n"
        "4. Do NOT verify or validate, just extract raw data.\n\n"
        "Example Output 1:\n"
        "[[1, 2, 3], [4, 0, 5], [6, 7, 8]];D\n\n"
        "Example Output 2:\n"
        "[[1, 2, 3], [4, 0, 5], [6, 7, 8]];{\"type\": \"rotate\", \"direction\": \"CW\", \"rectangle\": [0, 2, 1, 2], \"steps\": 1}\n\n"
        f"Reasoning Context:\n{reasoning_result}"
    )

    raw_response = call_llm_with_prompt(extraction_prompt)
    
    board_next = None
    move = None
    valid_extraction = False

    try:
        # 2. 清洗数据并按分号切分 (split maxsplit=1 防止 JSON 内部有分号干扰)
        clean_response = raw_response.strip().replace("```", "")  
        if ";" in clean_response:  
            board_str, move_str = clean_response.split(";", 1)  
            
            # 3. 解析 Board  
            extracted_board = ast.literal_eval(board_str.strip())  
            
            # 4. 解析 Move (如果是 JSON 字符串则不需要额外处理，如果是 U/D/L/R 也不需要)  
            move = move_str.strip()  
            
            # --- 严格校验逻辑 (Sanity Check) ---  
            if isinstance(extracted_board, list) and len(extracted_board) == 3:  
                if all(isinstance(row, list) and len(row) == 3 for row in extracted_board):  
                    flat_list = [num for row in extracted_board for num in row]  
                    if sorted(flat_list) == list(range(9)):  
                        board_next = extracted_board  
                        valid_extraction = True  

    except Exception as e:  
        print(f"Extraction failed: {e}")  
        print(f"Raw Response was: {raw_response}")  

    # 5. 错误处理与回退  
    if not valid_extraction:  
        print("⚠ Warning: Extraction format error or invalid board state. Keeping current state.")  
        board_next = deepcopy(board)  
        move = "ERROR" # 或者保留为 None  

    # 6. 更新 CW_bool (如果 move 是 JSON)  
    CW_bool = get_move_type_code(move) # 确保你的 get_move_type_code 能处理 JSON 字符串  

    print(f"\n🧩 Step: {step_type} Completed Board:")  
    print_board(board_next)  
    
    # 此时你可以很方便地将 board_next 和 move 存入 CSV  
    # csv_row = f'"{board_next}","{move}"'   
    
    return board_next, move, CW_bool  


def save_result(puzzle_id, final_board, total_moves, existing_results):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 仿照图片要求的字段进行记录
    result_data = {
        "id": puzzle_id,
        "solved": final_board==GOAL_STATE,
        "final_board": final_board,
        "total_steps": len(total_moves),
        "move_sequence": total_moves, # 对应图片的 steps/direction 概念
        "method": "LLM-Phased-Solver"
    }
    
    # 更新内存中的结果
    existing_results[puzzle_id] = result_data
    
    # 写入文件
    with open(OUTPUT_FILE, "w") as f:
        for pid, data in existing_results.items():
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

def parse_indices_input(input_str):
    indices = set()
    parts = input_str.strip().split()
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            indices.update(range(int(start), int(end)+1))
        else:
            indices.add(int(part))
    return sorted(indices)

def load_existing_results():
    results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    results[obj["id"]] = obj["solved"]
    return results

def update_csv_record(filename, pid, row_data):
    """
    读取现有CSV，更新指定pid的行，保持文件有序（按pid 0-19排序）。
    """
    # 1. 读取现有数据到字典中 {pid: row_content}
    data_map = {}
    if os.path.exists(filename):
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    try:
                        # 假设第一列是 ID
                        current_id = int(row[0])
                        data_map[current_id] = row
                    except ValueError:
                        continue # 跳过表头或无效行

    # 2. 更新当前计算结果
    data_map[pid] = row_data

    # 3. 按顺序（0到19）重写文件
    # 找出当前最大的ID，确保循环覆盖到所有已有的题
    max_id = max(data_map.keys()) if data_map else 19
    limit = max(20, max_id + 1)

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for i in range(limit):
            if i in data_map:
                writer.writerow(data_map[i])
            else:
                # 如果该题还没跑过，可以留空或者跳过，这里选择留空行占位，保持行号对应
                # writer.writerow([i, "Not Run Yet"]) 
                pass 

def main():
    # 加载数据
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # 兼容 Numpy 数组或 List
    boards = data.get("boards", [])
    import numpy as np
    if isinstance(boards, list):
        boards = np.array(boards)
    
    if len(boards) == 0:
        print("❌ 错误：没有找到题目数据 (boards)")
        return

    output_csv = "sliding_results.csv"
    print(f"📂 结果将保存至: {output_csv}")

    user_input = input("请输入要运行的题目编号 (e.g., 0,1,5 或 0-5): ")
    target_ids = parse_indices_input(user_input)

    for pid in target_ids:
        # 确保 pid 在有效范围内
        if pid < 0 or pid >= len(boards):
            print(f"⚠️ 跳过无效 ID: {pid}")
            continue

        # 提取初始棋盘 (确保转换为 Python list)
        board_current = boards[pid].tolist() if hasattr(boards[pid], 'tolist') else boards[pid]
        
        print(f"\n🚀 [ID={pid}] 开始解题...")
        # print("Initial board:")
        # print_board(board_current)

        # 记录历史：[ID, Board0, Move1, Board1, Move2, Board2, ...]
        # 注意：CSV第一列存 ID
        csv_row = [pid] 
        csv_row.append(str(board_current)) # 存入初始状态

        CW_bool = 0
        step_count = 0
        max_steps = 50 # 防止死循环的安全阈值

        while board_current != GOAL_STATE:
            if step_count >= max_steps:
                print(f"❌ 超过 {max_steps} 步未解出，强制停止。")
                break

            board_next, move, CW_bool = execute_step(board_current, CW_bool)
            
            # 交替追加：先动作，后状态
            csv_row.append(str(move))       # Move
            csv_row.append(str(board_next)) # Board
            
            board_current = board_next
            step_count += 1

        print(f"🎉 [ID={pid}] 解题完成! 共 {step_count} 步。")
        # print_board(board_current)
        
        # 实时保存到 CSV (防止程序崩溃丢失数据)
        update_csv_record(output_csv, pid, csv_row)
        print(f"💾 进度已保存至 CSV (Row {pid})")

if __name__ == "__main__":
    main()

