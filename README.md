# Crafter

Crafter is a Python-based framework designed to facilitate the creation and management of intelligent agents that can interact with users, execute Python code, and learn from past interactions. The framework includes several components, such as agents, a state machine, and a lesson extraction mechanism.

## Components

### Agents

1. **Agent**: The base class for all agents. It manages conversation history, interacts with a database to store and retrieve conversation data, and uses OpenAI's API to extract lessons from conversations.

2. **Coder**: A specialized agent that generates and executes Python code based on user input. It uses a chain-of-thought approach to iteratively develop and refine code solutions.

3. **Converser**: An agent that interacts with users to gather task requirements and constraints. It uses structured inquiry to ensure a comprehensive understanding of the user's needs.

### Tools

- **Exit Tool**: Used by agents to signal the end of a conversation.
- **Programmer Agent Tool**: Allows the agent to write, test, and execute Python code.
- **Python Interpreter Tool**: Executes Python scripts and returns the output.

### Graph

The `Graph` class implements a state machine to manage transitions between different states (nodes) based on input signals. Each node can store context-specific information, and transitions are defined by input symbols.

### Lesson Extraction

The framework includes functionality to extract lessons learned from past interactions using OpenAI's API. These lessons are stored in a database and can be used to improve future interactions.

## Usage

### Running the Framework

1. **Setup**: Ensure you have the necessary dependencies installed, including OpenAI's Python client and SQLite3.

2. **Execution**: Run the `run.py` script to start the framework. This script initializes the agents and the state machine, and begins processing user input.

3. **Lesson Extraction**: Use the `learn.py` script to extract lessons learned from past interactions. This script creates instances of each agent type and extracts lessons using OpenAI's API.

### Example

The `graph.py` file includes an example of how to use the `Graph` class to manage state transitions. The example demonstrates adding nodes, setting a start node, adding transitions, updating context, and processing input symbols.

## Logging

The framework uses Python's `logging` module to log important events and information. Logs are configured to display at the `INFO` level.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
