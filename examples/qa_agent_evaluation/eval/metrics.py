"""
Evaluation metrics for QA agent faithfulness assessment.

This module extracts evaluation data from processed traces and defines
metrics for measuring answer faithfulness and relevancy.
"""

import json
import ast
from typing import Dict, List, Optional
from pathlib import Path

from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM

from litellm import completion


class BedrockLLM(DeepEvalBaseLLM):
    """Custom DeepEval LLM using LiteLLM to call Bedrock."""

    def __init__(self, model: str = "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0"):
        self.model = model
        super().__init__(model)

    def load_model(self):
        """Load model - not needed for LiteLLM."""
        return self.model

    def generate(self, prompt: str) -> str:
        """Generate response using LiteLLM."""
        response = completion(model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0)
        return response.choices[0].message.content

    async def a_generate(self, prompt: str) -> str:
        """Async generate - use sync version."""
        return self.generate(prompt)

    def get_model_name(self) -> str:
        """Return model name."""
        return self.model


def extract_query_from_trace(trace_data: Dict) -> Optional[str]:
    """Extract the user query from trace data."""
    for span in trace_data.get("spans", []):
        if span.get("entity_name") == "invoke_agent" and span.get("gen_ai_prompts"):
            prompts = span["gen_ai_prompts"]
            if prompts and len(prompts) > 0:
                content = prompts[0].get("content", "")
                # Parse the content which is in format: '[{"text": "query"}]'
                try:
                    parsed = ast.literal_eval(content)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed[0].get("text", "")
                except:
                    pass
    return None


def extract_answer_from_trace(trace_data: Dict) -> Optional[str]:
    """Extract the final agent answer from trace data."""
    for span in trace_data.get("spans", []):
        if span.get("entity_name") == "invoke_agent" and span.get("gen_ai_completions"):
            completions = span["gen_ai_completions"]
            if completions and len(completions) > 0:
                return completions[0].get("content", "")
    return None


def extract_search_results_from_trace(trace_data: Dict) -> List[str]:
    """Extract search results (retrieval context) from trace data."""
    search_results = []

    for span in trace_data.get("spans", []):
        # Look for tool execution spans with web_search
        if span.get("entity_name") == "execute_tool" and span.get("gen_ai_tool_name") == "web_search":
            completions = span.get("gen_ai_completions", [])
            for completion in completions:
                if completion.get("role") == "assistant":
                    content = completion.get("content", "")
                    # Parse the search results
                    try:
                        # Content format: '[{"text": "[{\'title\': ..., \'content\': ...}]"}]'
                        parsed_outer = ast.literal_eval(content)
                        if isinstance(parsed_outer, list) and len(parsed_outer) > 0:
                            text_content = parsed_outer[0].get("text", "")
                            # Parse the inner list of search results
                            results = ast.literal_eval(text_content)
                            if isinstance(results, list):
                                for result in results:
                                    if isinstance(result, dict) and "content" in result:
                                        search_results.append(result["content"])
                    except Exception as e:
                        # If parsing fails, try simpler extraction
                        pass

    return search_results


def create_test_case_from_trace(trace_file: Path) -> Optional[LLMTestCase]:
    """Create a DeepEval LLMTestCase from a processed trace file."""
    try:
        with open(trace_file, "r") as f:
            trace_data = json.load(f)

        query = extract_query_from_trace(trace_data)
        answer = extract_answer_from_trace(trace_data)
        search_results = extract_search_results_from_trace(trace_data)
        print(f"  Extracted query: {query}")
        print(f"  Extracted answer: {answer}")
        print(f"  Extracted search results: {search_results}")
        exit()

        if not query or not answer:
            print(f"Warning: Could not extract query or answer from {trace_file.name}")
            return None

        if not search_results:
            print(f"Warning: No search results found in {trace_file.name}")
            return None

        # Create LLMTestCase with query, answer, and retrieval context (search results)
        test_case = LLMTestCase(input=query, actual_output=answer, retrieval_context=search_results)

        return test_case

    except Exception as e:
        print(f"Error processing trace file {trace_file}: {e}")
        return None


def create_faithfulness_metric(threshold: float = 0.7) -> FaithfulnessMetric:
    """
    Create a FaithfulnessMetric instance using Bedrock via LiteLLM.

    Args:
        threshold: Minimum score threshold (0-1)

    Returns:
        Configured FaithfulnessMetric instance
    """
    bedrock_llm = BedrockLLM()
    return FaithfulnessMetric(threshold=threshold, model=bedrock_llm, include_reason=True)


def create_answer_relevancy_metric(threshold: float = 0.7) -> AnswerRelevancyMetric:
    """
    Create an AnswerRelevancyMetric instance using Bedrock via LiteLLM.

    Args:
        threshold: Minimum score threshold (0-1)

    Returns:
        Configured AnswerRelevancyMetric instance
    """
    bedrock_llm = BedrockLLM()
    return AnswerRelevancyMetric(threshold=threshold, model=bedrock_llm, include_reason=True)
