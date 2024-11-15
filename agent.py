from dataclasses import Field
import json
import logging
import sqlite3
import subprocess
import sys
from typing import Dict
import uuid
from openai import OpenAI
import tempfile
import os
import shutil
import re

exit_tool = {
    "type": "function",
    "function": {
        "name": "exit",
        "strict": True,
        "description": "once you are done with your task, call this tool to end the conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "The ouput for your task",
                },
            },
            "required": ["output"],
            "additionalProperties": False,
        },
    }
}
    
programmer_agent_tool = {
    "type": "function",
    "function": {
        "name": "programmer",
        "strict": True,
        "description": "Once you are done gathering the task requirements, call this tool to write, test, and execute python code. It will return the output of the code.",
        "parameters": {
             "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "The ouput for your task",
                },
            },
            "required": ["output"],
            "additionalProperties": False,
        }
    }
}



python_interpreter_tool = {
    "type": "function",
    "function": {
        "name": "execute_code",
        "strict": True,
        "description": "Execute python script and return the standard output.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code snippet to be executed.",
                },
            },
            "required": ["code"],
            "additionalProperties": False,
        },
    }
}


class Agent:
    def __init__(self, prompt: str, instance_id=None, tools: list[dict] = []):
        self.db_connection = sqlite3.connect('conversation_history.db')
        self.agent_type = self.__class__.__name__  # Store the agent type
        self._initialize_db()

        self.tools = [exit_tool] + tools

        if instance_id:
            self.instance_id = instance_id
            self.conversation_history = self._load_conversation_history()
        else:
            self.instance_id = str(uuid.uuid4())  # Generate a new unique ID
            prompt = prompt + """
Consider lessons learned from previous interactions to enhance your approach. 
Integrate these insights into your chain of thought and responses to better serve the user.

Lessons learned: 
{lessons}

Consider the following tools: 
{tools}
            """
            final_prompt = prompt.format(
                lessons="\n".join(self.load_learned_lessons()), 
                tools="\n".join([f"{tool['function']['name']}: {tool['function']['description']}" for tool in self.tools])
            )
            self.conversation_history = [
                {"role": "system", "content": final_prompt}
            ]
        
        self.openai = OpenAI()
        self.logger = logging.getLogger(f"{str(self.instance_id)} - {__name__}")
        self.logger.info(f"created agent with instance_id: {str(self.instance_id)}")
        self.logger.info(f"tools: {self.tools}")
        self.logger.info(f"prompt: {final_prompt}")

    def _initialize_db(self):
        with self.db_connection:
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            ''')
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS lessons_learned (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_type TEXT NOT NULL,
                    lesson TEXT NOT NULL
                )
            ''')

    def _load_conversation_history(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT role, content FROM conversation_history WHERE instance_id = ?
        ''', (self.instance_id,))
        rows = cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]


    def add_message_to_history(self, role: str, content: str):
        # Add message to conversation history
        self.logger.info(f"adding message to history: {role}, {content}")
        self.conversation_history.append({"role": role, "content": content})
        
        # Insert message into SQLite database with instance_id and agent_type
        with self.db_connection:
            self.db_connection.execute('''
                INSERT INTO conversation_history (instance_id, agent_type, role, content) VALUES (?, ?, ?, ?)
            ''', (self.instance_id, self.agent_type, role, content))

    def extract_lessons_from_messages(self, messages):
        prompt = """
        You are an expert at extracting lessons from conversations.
        Do not invent lessons, only extract the ones that are explicitly stated.
        Be succinct, only extract the lessons that are most important to the task at hand.
        Extract the lessons from the following conversation:
        {messages}  
        """
        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt.format(messages="\n".join(messages))}],
        )
        return response.choices[0].message.content

    def extract_lessons_learned(self):
        with self.db_connection:
            cursor = self.db_connection.execute('''
                SELECT content FROM conversation_history
                WHERE agent_type = ?
            ''', (self.agent_type,))
            messages = [row[0] for row in cursor.fetchall()]

        # Use OpenAI to extract lessons learned
        lessons = self.extract_lessons_from_messages(messages)
        self.logger.info(f"extracted lessons for agent {self.agent_type}: {lessons}")
        
        # Save lessons to the database
        with self.db_connection:
            self.db_connection.execute('''
                INSERT INTO lessons_learned (agent_type, lesson)
                    VALUES (?, ?)
                ''', (self.agent_type, lessons))

    def run(self, input):
        pass

    def load_learned_lessons(self) -> list[str]:
        """Load learned lessons for the current agent type."""
        with self.db_connection:
            cursor = self.db_connection.execute('''
                SELECT lesson FROM lessons_learned
                WHERE agent_type = ?
            ''', (self.agent_type,))
            lessons = [row[0] for row in cursor.fetchall()]

        return lessons




class Coder(Agent):

    def __init__(self, prompt: str =None, instance_id=None):
        # prompt = ("You are an AI capable of generating and running Python code to solve user questions. "
        #         "Use a chain-of-thought approach to produce code step-by-step, analyzing results after each execution."
        #         "When you believe you have a working solution, execute the code using the appropriate tool."
        #         "If further refinement is needed, continue improving the code until the solution is accurate."
        #         "Ensure the output of the script answers the user's question."
        #         "Only return Python code snippets for execution throughout the process, focusing on producing a correct and complete solution."
        #         "Your python code snippets should print out the solution on stadard output."
        #         )
        prompt = """
        You are an AI capable of generating and running Python code to solve user questions. 
        Follow a chain-of-thought approach to break down the solution into logical steps, producing Python code incrementally.
        For each step, execute the code using the appropriate tool, analyze the resulting output, and refine the code as needed.
        1.	Begin by crafting a Python script based on the user’s question.
        2.	Run the script and analyze the output returned by the tool, assessing whether it meets the user’s requirements.
        3.	If the output is unsatisfactory, identify areas for improvement, adjust the script, and execute it again.
        4.	Repeat this iterative process, refining the code and re-running it as necessary, until the final output fully addresses the user’s question.

        Return only the Python code snippets intended for execution. Ensure that the final script prints the solution clearly on standard output, 
        fulfilling all requirements accurately and completely.
        """
        super().__init__(prompt=prompt, instance_id=instance_id, tools=[python_interpreter_tool])
        self.execution_dir = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))
        
        # Set up a virtual environment in the execution directory
        subprocess.run([sys.executable, "-m", "venv", self.execution_dir])

    def __del__(self):
        # Clean up the temporary directory when the object is destroyed
        if os.path.exists(self.execution_dir):
            shutil.rmtree(self.execution_dir)

    def execute_code(self, code):
        import subprocess
        import sys
        import os
        import re

        try:
            # Create a temporary file to store the code in the execution directory
            code_file_path = os.path.join(self.execution_dir, "script.py")
            with open(code_file_path, "w") as code_file:
                code_file.write(code)

            # Extract import statements to determine required packages
            imports = re.findall(r'^\s*import (\S+)|^\s*from (\S+) import', code, re.MULTILINE)
            packages = {imp[0] or imp[1] for imp in imports}

            # Activate the virtual environment and install packages
            pip_executable = os.path.join(self.execution_dir, 'bin', 'pip') if os.name != 'nt' else os.path.join(self.execution_dir, 'Scripts', 'pip.exe')
            for package in packages:
                subprocess.run([pip_executable, "install", package], check=True)

            # Run the code in a subprocess with the virtual environment
            python_executable = os.path.join(self.execution_dir, 'bin', 'python') if os.name != 'nt' else os.path.join(self.execution_dir, 'Scripts', 'python.exe')
            result = subprocess.run(
                [python_executable, code_file_path],
                capture_output=True,
                text=True,
                cwd=self.execution_dir
            )

            # Return the output or error
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def run(self, input = str, context: dict = None) -> tuple[str, str]:
        self.add_message_to_history("user", input)
        for _ in range(1024):  # Limit to 10 iterations to avoid infinite loops

            response = self.openai.beta.chat.completions.parse(
                model="gpt-4o",  # Replace with the model you are using, e.g., gpt-3.5-turbo
                messages=self.conversation_history,
                #response_format=ContextObject,
                tools=self.tools, 
                temperature=0.0
            )
            if response.choices[0].message.tool_calls:

                for tool_call in response.choices[0].message.tool_calls:
                    if tool_call.function.name == "exit":
                        self.add_message_to_history("assistant", json.dumps( {'function': tool_call.function.name, 'arguments': tool_call.function.arguments }))
                        args = json.loads(tool_call.function.arguments)
                        return "exit", args['output']
                    elif tool_call.function.name == "execute_code":
                        self.add_message_to_history("assistant", json.dumps( {'function': tool_call.function.name, 'arguments': tool_call.function.arguments }))
                        # arguments: "{\"code\":\"def fibonacci(n):\\n    a, b = 0, 1\\n    for _ in range(n):\\n        a, b = b, a + b\\n    return a\\n\\n# Get the 145th Fibonacci number\\nfibonacci_145 = fibonacci(145)\\nfibonacci_145\"}"
                        args = json.loads(tool_call.function.arguments)
                        self.logger.info(f"executing code: {args['code']}")
                        execution_output = self.execute_code(args['code'])
                        if execution_output.strip() == "":
                            output = "No standard output was produced. We expect the code to produce a result."
                        else:
                            output = f" {execution_output}"
                        self.add_message_to_history("user", execution_output)

class Converser(Agent):
    def __init__(self, user_interface, prompt: str =None, instance_id=None):
        self.user_interface = user_interface;
        prompt = """You are an intelligent assistant that interacts with users to clarify and gather specific requirements and constraints for any task the user needs help with. Your objective is to engage the user in a structured conversation to fully understand the details of their request, without making any assumptions about the task itself.

Instructions:
	1.	Acknowledge the User’s Request
Begin by acknowledging the user’s request, regardless of its nature. For example, if the user asks, “How much do I need to save for retirement?” respond with, “I’d be happy to help with that. Let’s go over a few details first.”
	2.	Structured Inquiry
Ask relevant questions, one at a time, to gather a clear picture of the user’s requirements and constraints. Use the following approach:
	•	Open-Ended Questions: Start with questions that encourage the user to share more context (e.g., “Could you tell me more about what you’re trying to accomplish?”).
	•	Targeted Questions: As you learn more, ask specific questions tailored to the user’s answers, ensuring each question aligns with the task’s needs.
	3.	Active Listening
Wait for the user’s response to each question before proceeding, and adjust your inquiries based on their input.
	4.	Avoid Assumptions
Your role is solely to gather information, so do not perform any calculations or estimations. Calculations or estimations will be handled by an external tool.
	5.	Tool Selection
Once all necessary information is gathered, confirm with the user that you have everything needed. After receiving confirmation, select the most appropriate tool from the list provided at runtime based on the gathered data, and pass along the problem description and relevant data to complete the task.
	6.	Polite and Clear Guidance
Throughout, maintain a polite and clear tone, guiding the user through each question to avoid overwhelming them.

    """
        super().__init__(prompt=prompt, instance_id=instance_id, tools=[programmer_agent_tool])
        

    def run(self, input = str, context: dict = None) -> tuple[str, str]:
        if input:
            self.add_message_to_history("user", input)

        for k in range(1024):  # Limit iterations to avoid infinite loops

            response = self.openai.chat.completions.create(
                model="gpt-4o",  # Replace with the model you are using, e.g., gpt-3.5-turbo
                messages=self.conversation_history,
                tools=self.tools, 
                temperature=0.0
            )
            

            if response.choices[0].message.tool_calls:
                
                for tool_call in response.choices[0].message.tool_calls:

                    if tool_call.function.name == "programmer":
                        self.add_message_to_history("assistant", json.dumps( {'function': tool_call.function.name, 'arguments': tool_call.function.arguments }))
                        args = json.loads(tool_call.function.arguments)
                        return "programmer", args['output']
                    elif tool_call.function.name == "exit":
                        self.add_message_to_history("assistant", json.dumps( {'function': tool_call.function.name, 'arguments': tool_call.function.arguments }))
                        args = json.loads(tool_call.function.arguments)
                        return "exit", args['output']
                    else:
                        raise Exception(f"{self.instance_id} - Unknown tool call: {tool_call.function.name}")

            assistant_message = response.choices[0].message.content
            
            self.add_message_to_history("assistant", assistant_message)
            
            user_input = self.user_interface(assistant_message)
            
            self.add_message_to_history("user", user_input)

        raise Exception("Max iterations reached")