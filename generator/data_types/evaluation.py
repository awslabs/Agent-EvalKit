from typing_extensions import TypedDict


class Interaction(TypedDict, total=False):
    """
    Represents a single interaction in a multi-agent or multi-step system.

    Used to capture the communication flow and dependencies between different
    components (agents, tools, or processing nodes) during task execution.
    All fields are optional to accommodate different interaction patterns.

    Attributes:
        node_name: Identifier for the agent, tool, or component involved in this interaction
        dependencies: List of other nodes/components this interaction depends on or references
        messages: Sequence of messages, responses, or communication exchanged during this interaction

    Example:
        interaction = {
            "node_name": "calculator_agent",
            "dependencies": ["input_parser", "math_validator"],
            "messages": ["Calculate 2+2"]
        }
    """

    node_name: str
    dependencies: list
    messages: list
