import json
import os
import logging
from abc import ABC, abstractmethod
from util.compress_file import get_skeleton
from util.postprocess_data import extract_code_blocks, extract_locs_for_files
from util.preprocess_data import (
    get_full_file_paths_and_classes_and_functions,
    get_repo_files,
    line_wrap_content,
    show_project_structure,
    filter_none_python
)
from util._repo_structure import create_structure
from util.api_requests import (
    create_chatgpt_config,
    num_tokens_from_messages,
    request_chatgpt_engine,
)
class LocalizeFunctions:
    def __init__(self, max_tokens: int = 1000):
        self.max_tokens = max_tokens
        self.obtain_relevant_files_prompt = """
        Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem.

        ### GitHub Problem Description ###
        {problem_statement}

        ###

        ### Repository Structure ###
        {structure}

        ###

        Please only provide the full path and return at most 5 files.
        The returned files should be separated by new lines ordered by most to least important and wrapped with ```
        For example:
        ```
        file1.py
        file2.py
        ```
        """

    def _parse_model_return_lines(self, content: str) -> list[str]:
            return content.strip().split("\n")

    def localize_files(self, problem_statement, top_n) -> tuple[list, list, list, any]:

        # get structure
        structure = create_structure(".")
        filter_none_python(structure)
        # filter_out_test_files(structure) #NOTE: should only do this for non pytest files

        found_files = []
        additional_artifact_loc_file = None
        file_traj = {}
        message = self.obtain_relevant_files_prompt.format(
            problem_statement=problem_statement,
            structure=show_project_structure(structure).strip(),
        ).strip()

        print(f"prompting with message:\n{message}")
        print("=" * 80)

        config = create_chatgpt_config(
            message=message,
            max_tokens=self.max_tokens,
            temperature=0,
            batch_size=1,
            model="gpt-4o-2024-05-13",  # use gpt-4o for now.
        )


        ret = request_chatgpt_engine(config)
        raw_output = ret.choices[0].message.content
        traj = {
            "prompt": message,
            "response": raw_output,
            "usage": {
                "prompt_tokens": ret.usage.prompt_tokens,
                "completion_tokens": ret.usage.completion_tokens,
            },
        }
        model_found_files = self._parse_model_return_lines(raw_output)
        
        files, classes, functions = get_full_file_paths_and_classes_and_functions(
            structure
        )

        for file_content in files:
            file = file_content[0]
            if file in model_found_files:
                found_files.append(file)

        # sort based on order of appearance in model_found_files
        found_files = sorted(found_files, key=lambda x: model_found_files.index(x))

        print(raw_output)

        return (
            found_files,
            {"raw_output_files": raw_output},
            traj,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Localize files")
    parser.add_argument("problem_statement", type=str, help="The problem statement")
    parser.add_argument(
        "--top_n",
        type=int,
        default=5,
        help="The number of files to return",
    )
    parser.add_argument("repo_dir", type=str, help='')
    args = parser.parse_args()


    LF = LocalizeFiles()
    LF.localize_files(args.problem_statement, args.top_n)