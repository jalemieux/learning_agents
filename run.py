


import json
import time
from agent import Agent, Converser, Coder

import logging

from graph import Graph




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def user_interface(text):
    logger.info(f"user_interface: {text}")
    user_input = input(f"\033[1m{text}\033[0m\n")
    logger.info(f"user_input: {user_input}")
    return user_input
    

convo = Converser(user_interface=user_interface)
programmer = Coder()

init = None
end = None
g = Graph()
g.add_node(convo)
g.add_node(programmer)
g.add_node(init)
g.add_node(end)
g.add_transition(init, 'start', convo)
g.add_transition(convo, 'programmer', programmer)
g.add_transition(programmer, 'exit', convo)
g.add_transition(convo, 'exit', end)
g.set_start_node(init)

message = json.dumps({})
ctx = {}
signal = 'start'
while True:
    new_node = g.process_input(signal)
    time.sleep(1)
    if issubclass(type(new_node.object), Agent):
        signal, message = new_node.object.run(message, ctx)
    else:
        logger.info(f"New node is not an Agent: {new_node.__class__.__name__}")





# f(curretns tate, signal) = new state
