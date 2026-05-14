EXECUTE_WORKFLOW_TEMPLATE = """Please strictly follow the steps required in the Workflow, starting from the Input to obtain the Output.  
Input: {input}  
Output: {output}  
Workflow: {workflow}"""

STANDARD_TEMPLATE="""Fill the Sudoku board.Each row, each column, and each 2×3 block must contain the digits 1 through 6 exactly once, with no repetitions in any unit.
Input: {input}
"""