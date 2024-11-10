class Node:
    def __init__(self, object):
        self.object = object
        self.transitions = {}
        self.context = {}  # Add a context attribute to store node-specific information

    def add_transition(self, input_symbol, next_node):
        """Adds a transition to another state"""
        self.transitions[input_symbol] = next_node

    def get_next_node(self, input_symbol):
        """Gets the next node based on the input symbol"""
        return self.transitions.get(input_symbol, None)

class Graph:
    def __init__(self):
        self.nodes = {}
        self.current_node = None

    def add_node(self, node_name):
        """Creates a new node and adds it to the state machine"""
        node = Node(node_name)
        self.nodes[node_name] = node
        if self.current_node is None:
            self.current_node = node  # Set the initial state

    def set_start_node(self, node_name):
        """Sets the starting node of the state machine"""
        if node_name in self.nodes:
            self.current_node = self.nodes[node_name]

    def add_transition(self, from_node, input_symbol, to_node):
        """Adds a transition between two states based on an input symbol"""
        if from_node in self.nodes and to_node in self.nodes:
            self.nodes[from_node].add_transition(input_symbol, self.nodes[to_node])

    def process_input(self, input_symbol) -> Node:
        """Processes an input symbol and moves to the next state if possible"""
        if self.current_node:
            next_node = self.current_node.get_next_node(input_symbol)
            if next_node:
                print(f"Transitioning from {self.current_node.object.__class__.__name__} to {next_node.object.__class__.__name__} on '{input_symbol}'")
                self.current_node = next_node
                return self.current_node
            
            else:
                print(f"No transition found for input '{input_symbol}' from state {self.current_node.object.__class__.__name__}")
        else:
            print("State machine is not initialized with a start state.")

    def update_context(self, key, value):
        """Updates the context of the current node"""
        if self.current_node:
            self.current_node.context[key] = value
            print(f"Updated context for {self.current_node.name}: {self.current_node.context}")
        else:
            print("No current node to update context.")

    def get_context(self):
        """Returns the context of the current node"""
        if self.current_node:
            return self.current_node.context
        else:
            print("No current node to get context from.")
            return None

# Example usage
if __name__ == "__main__":
    sm = Graph()

    # Add states
    sm.add_node("Idle")
    sm.add_node("Processing")
    sm.add_node("Complete")

    # Set start state
    sm.set_start_node("Idle")

    # Add transitions
    sm.add_transition("Idle", "start", "Processing")
    sm.add_transition("Processing", "finish", "Complete")
    sm.add_transition("Complete", "reset", "Idle")

    # Update context
    sm.update_context("status", "waiting")
    print(sm.get_context())  # Output: {'status': 'waiting'}

    # Process inputs
    sm.process_input("start")       # Transition from Idle to Processing
    sm.update_context("status", "in progress")
    print(sm.get_context())  # Output: {'status': 'in progress'}

    sm.process_input("finish")      # Transition from Processing to Complete
    sm.update_context("status", "done")
    print(sm.get_context())  # Output: {'status': 'done'}

    sm.process_input("reset")       # Transition from Complete to Idle
    sm.update_context("status", "waiting")
    print(sm.get_context())  # Output: {'status': 'waiting'}

    sm.process_input("invalid")     # No transition from Idle on 'invalid' 