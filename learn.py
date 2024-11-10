import logging
from agent import Coder, Converser
# Assuming you have imported the necessary classes and set up your environment
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_lesson_learned_extraction():
    # Create instances of each agent type
    coder_agent = Coder(prompt="Coder prompt")
    converser_agent = Converser(user_interface=lambda x: x, prompt="Converser prompt")

    # Extract lessons learned for each agent type
    coder_agent.extract_lessons_learned()
    converser_agent.extract_lessons_learned()

    print("Lessons learned extraction completed for all agent types.")

# Run the extraction process
if __name__ == "__main__":
    execute_lesson_learned_extraction()