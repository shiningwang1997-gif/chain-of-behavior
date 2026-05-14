EXECUTE_WORKFLOW_TEMPLATE = """Please strictly follow the steps required in the Workflow, starting from the Input to obtain the Output.  
Input: {input}  
Output: {output}  
Workflow: {workflow}"""

STANDARD_TEMPLATE = """Solve the 3×3 sliding puzzle (8-puzzle).

Rules:
- The board is a 3×3 grid containing numbers 1–8 and a single empty cell represented by 0.
- A move consists of swapping 0 with one of its adjacent cells.
- Valid moves are:
  U: move 0 up
  D: move 0 down
  L: move 0 left
  R: move 0 right

Goal:
Transform the given board into the target board:
[[1,2,3],
 [4,5,6],
 [7,8,0]]

Output requirements:
- Output ONLY a sequence of characters from {U, D, L, R}.
- The sequence must be based on 0 as the moving tile.
- Do NOT include explanations, comments, or extra text.
- The final board after applying the sequence must exactly match the target board.

Input: {input}
"""
