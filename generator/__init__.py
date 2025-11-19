"""
Dataset Generator for Agent-EvalKit

Provides LLM-based test case generation with optional topic planning.
Requires: pip install strands-agents strands-agents-tools
"""

from .dataset_generator import DatasetGenerator
from .topic_planner import TopicPlanner
from .case import Case
from .dataset import Dataset

__all__ = [
    "DatasetGenerator",
    "TopicPlanner",
    "Case",
    "Dataset"
]
