# prompts/prompt_templates.py

COT_24_TEMPLATE = """You are an AI reasoning agent.    

Think step by step:  
- Describe how each number relates to 24 (larger, smaller, divisor, multiple, complement).  
- Consider which numbers seem more suitable for scaling, which ones are better for adjustment, and which could serve as neutral elements.  
- Avoid describing direct actions like “combine” or “multiply”; instead, use conceptual language such as “this number has the role of scaling”, “this pair creates balance”, or “this relation suggests proximity to 24”.  
- Only at the end, after reasoning, present a final expression that achieves 24 in the following format: Answer: <expression> = 24  

Example:

Input: 4 4 6 8  

Step 1: Among the numbers, 8 and 6 stand out as the largest, and their relation to 24 is that both are divisors (24 ÷ 6 = 4, 24 ÷ 8 = 3). They may provide structure.  
Step 2: The number 4 is directly one quarter of 24, suggesting it could play a role in proportional reasoning.  
Step 3: A difference of 2 (from 6 and 4) appears useful as a scaling factor.  
Step 4: With 12 (from 4 and 8) and the factor 2, the pathway to 24 becomes evident.  

Answer: (6 - 4) * (4 + 8) = 24  

Input: 2 9 10 12  

Step 1: The number 12 is exactly half of 24, so it seems naturally aligned.  
Step 2: The number 2 is a natural partner to 12, since their relation produces 24 directly.  
Step 3: The pair (10, 9) is close, producing a small difference that can serve as a neutralizing adjustment.  
Step 4: This relational structure supports a valid solution.  

Answer: 12 * 2 * (10 - 9) = 24  

Input: {input}  

Answer:"""




WF_24_TEMPLATE = """You are a workflow design expert. Based on the following task information, please design a workflow:

Task Information:
{Use numbers and basic arithmetic operations + - * / ( ) to obtain 24.
Input: 4 4 6 8
Answer: (4 + 8) * (6 - 4) = 24
Input: 2 9 10 12
Answer: 2 * 12 * (10 - 9) = 24
Input: 4 9 10 13
Answer: (13 - 9) * (10 - 4) = 24
Input: 1 4 8 8
Answer: (8 / 4 + 1) * 8 = 24
Input: 5 5 5 9
Answer: 5 + 5 + 5 + 9 = 24
Input: 
}

Please analyze this task, break it down into a logically clear sequence of steps, and design a workflow that can be executed by functions.

Output Requirement:
Include the complete sequence of steps, and output in the following format without any additional explanation.

Step {Step number}  
- Input: {Input description}  
- Output: {Output description}  
- Execution: {Method and process} 

"""



EXECUTE_WORKFLOW_TEMPLATE = """Please strictly follow the steps required in the Workflow, starting from the Input to obtain the Output.  
Input: {input}  
Output: {output}  
Workflow: {workflow}"""

