import logging
from agent import Converser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define a simple user interface function for demonstration purposes
def user_interface(message):
    print(f"Assistant: {message}")
    return input("User: ")

# Initialize the Converser agent
converser_agent = Converser(user_interface=user_interface)

# Call the run method with an example input
output_type, output_content = converser_agent.run("I need help with a task.")

# Print the output
logger.info(f"Output Type: {output_type}")
logger.info(f"Output Content: {output_content}")