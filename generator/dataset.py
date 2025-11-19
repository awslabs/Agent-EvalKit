import json
import os
from typing_extensions import Generic, TypeVar

from .case import Case

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Dataset(Generic[InputT, OutputT]):
    """
    A collection of test cases, representing a dataset.

    Dataset organizes a collection of test cases for evaluation purposes.

    Attributes:
        cases: A list of test cases in the dataset.

    Example:
        dataset = Dataset[str, str](
            cases=[
                Case(name="Simple Knowledge",
                        input="What is the capital of France?",
                        expected_output="The capital of France is Paris.",
                        metadata={"category": "knowledge"}),
               Case(name="Simple Math",
                        input="What is 2x2?",
                        expected_output="2x2 is 4.",
                        metadata={"category": "math"})
            ]
        )
    """

    def __init__(
        self,
        cases: list[Case[InputT, OutputT]] | None = None,
    ):
        self._cases = cases or []

    @property
    def cases(self) -> list[Case[InputT, OutputT]]:
        """
        Get a deep copy of all test cases in the dataset.

        Returns deep copies to prevent accidental mutation of the original test cases.
        Users can safely modify the returned cases without affecting the dataset.

        Returns:
            List of Case objects (deep copies) containing all test cases in the dataset
        """
        return [case.model_copy(deep=True) for case in self._cases]

    @cases.setter
    def cases(self, new_cases: list[Case[InputT, OutputT]]):
        """
        Set the test cases for this dataset.

        Args:
            new_cases: List of Case objects to use as the dataset's test cases
        """
        self._cases = new_cases

    def to_file(self, file_name: str, format: str = "json", directory: str = "eval"):
        """
        Write the dataset to a file in JSONL format.

        Args:
            file_name: Name of the file without extension.
            format: The format of the file to be saved (currently only "json" supported).
            directory: Directory to save the file (default: "eval").
        """
        os.makedirs(directory, exist_ok=True)
        if format == "json":
            # Save as JSONL (one case per line)
            with open(f"{directory}/{file_name}.jsonl", "w") as f:
                for case in self._cases:
                    f.write(json.dumps(case.model_dump()) + "\n")
        else:
            raise Exception(f"Format {format} is not supported.")

    @classmethod
    def from_file(cls, file_path: str, format: str = "json"):
        """
        Create a dataset from a JSONL file.

        Args:
            file_path: Path to the file.
            format: The format of the file to be read (currently only "json" supported).

        Return:
            A Dataset object.
        """
        if format == "json":
            cases: list[Case] = []
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        case_data = json.loads(line)
                        cases.append(Case.model_validate(case_data))
            return cls(cases=cases)
        else:
            raise Exception(f"Format {format} is not supported.")
