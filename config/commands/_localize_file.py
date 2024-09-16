#!/usr/bin/env python3
# @yaml
# signature: _localize_file <problem_statement> <repo_dir> <top_n>
# docstring: Localize the top N most suspicious files related to the problem statement in the given repository.
# arguments:
#   problem_statement:
#     type: string
#     description: The problem statement or issue text
#     required: true
#   repo_dir:
#     type: string
#     description: The directory of the repository to search in
#     required: true
#   top_n:
#     type: int
#     description: The number of suspicious files to return
#     required: true

"""This helper command is used to localize to the top N suspicious files that are related to the problem statement.

Usage:
    python _localize_file.py <problem_statement> <repo_dir> <top_n> 

Where:
    <problem_statement> is the problem statement
    <repo_dir> is the repository directory
    <top_n> is the number of files to return
"""

import json
import os
import sys
import logging
import re
import ast
from typing import List, Dict, Any, Tuple
import signal
import time
import openai
import config
import libcst as cst
import libcst.matchers as m

print("localize_file.py is being used...")

cfg = config.Config(os.path.join(os.getcwd(), "keys.cfg"))
client = openai.OpenAI(api_key=cfg['OPENAI_API_KEY'])

# Incorporating necessary functions from other modules
def get_skeleton(raw_code, keep_constant: bool = True):
    try:
        tree = cst.parse_module(raw_code)
    except:
        return raw_code

    transformer = CompressTransformer(keep_constant=keep_constant)
    modified_tree = tree.visit(transformer)
    code = modified_tree.code
    code = code.replace(CompressTransformer.replacement_string + "\n", "...\n")
    code = code.replace(CompressTransformer.replacement_string, "...\n")
    return code


def extract_code_blocks(text):
    pattern = r"```\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    if len(matches) == 0:
        if "```" in text:
            # handle the case where the code block is not complete
            return [text.split("```", 1)[-1].strip()]
    return matches


def extract_locs_for_files(locs, file_names):
    # TODO: keep the order from this fine-grained FL results.
    results = {fn: [] for fn in file_names} # dictionary with file names as the keys
    with open("localize_related.txt", "a") as f:
        f.write("Results Dict (contains filenames)\n" + str(results) + "\n"*3)
        f.write("Locs:\n" + str(locs) + "\n"*3)

    current_file_name = None
    for loc in locs:
        for line in loc.splitlines():

            with open("localize_related.txt", "a") as f:
                f.write("Current Line:\n" + str(line) + "\n")
                f.write("processed: " + str(line.strip().split(" ")[1]) + "\n") 

            if line.strip().endswith(".py"):
                current_file_name = line.strip().split(" ")[1]
              
            elif line.strip() and any(
                line.startswith(w)
                for w in ["line:", "function:", "class:", "variable:", "path:"] # add a path 
            ):
                if current_file_name in results: # only take file name in results 
                    with open("localize_related.txt", "a") as f:
                        f.write("Curr filename found in results\n")
                    results[current_file_name].append(line)
                else:
                    pass
    output = [["\n".join(results[fn])] for fn in file_names]
    return output

def create_structure(directory_path):
    """ 这是最重要的函数    
    Create the structure of the repository directory by parsing Python files.
    :param directory_path: Path to the repository directory.
    :return: A dictionary representing the structure.
    """
    structure = {}

    for root, _, files in os.walk(directory_path):
        repo_name = os.path.basename(directory_path)
        relative_root = os.path.relpath(root, directory_path)
        if relative_root == ".":
            relative_root = repo_name
        curr_struct = structure
        for part in relative_root.split(os.sep):
            if part not in curr_struct:
                curr_struct[part] = {}
            curr_struct = curr_struct[part]
        for file_name in files:
            if file_name.endswith(".py"):
                file_path = os.path.join(root, file_name)
                class_info, function_names, file_lines = parse_python_file(file_path)
                curr_struct[file_name] = {
                    "classes": class_info,
                    "functions": function_names,
                    "text": file_lines,
                }
            else:
                curr_struct[file_name] = {}

    return structure


def parse_python_file(file_path, file_content=None):
    """Parse a Python file to extract class and function definitions with their line numbers.
    :param file_path: Path to the Python file.
    :return: Class names, function names, and file contents
    """
    if file_content is None:
        try:
            with open(file_path, "r") as file:
                file_content = file.read()
                parsed_data = ast.parse(file_content)
        except Exception as e:  # Catch all types of exceptions
            print(f"Error in file {file_path}: {e}")
            return [], [], ""
    else:
        try:
            parsed_data = ast.parse(file_content)
        except Exception as e:  # Catch all types of exceptions
            print(f"Error in file {file_path}: {e}")
            return [], [], ""

    class_info = []
    function_names = []
    class_methods = set()

    for node in ast.walk(parsed_data):
        if isinstance(node, ast.ClassDef):
            methods = []
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    methods.append(
                        {
                            "name": n.name,
                            "start_line": n.lineno,
                            "end_line": n.end_lineno,
                            "text": file_content.splitlines()[
                                n.lineno - 1 : n.end_lineno
                            ],
                        }
                    )
                    class_methods.add(n.name)
            class_info.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "text": file_content.splitlines()[
                        node.lineno - 1 : node.end_lineno
                    ],
                    "methods": methods,
                }
            )
        elif isinstance(node, ast.FunctionDef) and not isinstance(
            node, ast.AsyncFunctionDef
        ):
            if node.name not in class_methods:
                function_names.append(
                    {
                        "name": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "text": file_content.splitlines()[
                            node.lineno - 1 : node.end_lineno
                        ],
                    }
                )

    return class_info, function_names, file_content.splitlines()

def filter_none_python(structure: Dict[str, Any]) -> None:
    # Remove non-Python files from the structure
    for key, value in list(structure.items()):
        if isinstance(value, dict):
            if "type" in value and value["type"] == "file":
                if not key.endswith('.py'):
                    del structure[key]
            else:
                filter_none_python(value)
                if not value:
                    del structure[key]

def show_project_structure(structure: Dict[str, Any], spacing: int = 0) -> str:
    result = ""
    for key, value in structure.items():
        result += " " * spacing + key + "\n"
        if isinstance(value, dict) and "type" not in value:
            result += show_project_structure(value, spacing + 2)
    return result

def get_full_file_paths_and_classes_and_functions(structure, current_path=""):
    """
    Recursively retrieve all file paths, classes, and functions within a directory structure.

    Arguments:
    structure -- a dictionary representing the directory structure
    current_path -- the path accumulated so far, used during recursion (default="")

    Returns:
    A tuple containing:
    - files: list of full file paths
    - classes: list of class details with file paths
    - functions: list of function details with file paths
    """
    files = []
    classes = []
    functions = []
    for name, content in structure.items():
        if isinstance(content, dict):
            if (
                not "functions" in content.keys()
                and not "classes" in content.keys()
                and not "text" in content.keys()
            ) or not len(content.keys()) == 3:
                # or guards against case where functions and classes are somehow part of the structure.
                next_path = f"{current_path}/{name}" if current_path else name
                (
                    sub_files,
                    sub_classes,
                    sub_functions,
                ) = get_full_file_paths_and_classes_and_functions(content, next_path)
                files.extend(sub_files)
                classes.extend(sub_classes)
                functions.extend(sub_functions)
            else:
                next_path = f"{current_path}/{name}" if current_path else name
                files.append((next_path, content["text"]))
                if "classes" in content:
                    for clazz in content["classes"]:
                        classes.append(
                            {
                                "file": next_path,
                                "name": clazz["name"],
                                "start_line": clazz["start_line"],
                                "end_line": clazz["end_line"],
                                "methods": [
                                    {
                                        "name": method["name"],
                                        "start_line": method["start_line"],
                                        "end_line": method["end_line"],
                                    }
                                    for method in clazz.get("methods", [])
                                ],
                            }
                        )
                if "functions" in content:
                    for function in content["functions"]:
                        function["file"] = next_path
                        functions.append(function)
        else:
            next_path = f"{current_path}/{name}" if current_path else name
            files.append(next_path)
    return files, classes, functions

def create_chatgpt_config(message: str, max_tokens: int, temperature: float, batch_size: int, model: str) -> Dict[str, Any]:
    # Simplified config creation
    return {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

def request_chatgpt_engine(config):
    ret = None
    while ret is None:
        try:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(100)
            ret = client.chat.completions.create(**config)
            signal.alarm(0)
        except openai._exceptions.BadRequestError as e:
            print(e)
            signal.alarm(0)
        except openai._exceptions.RateLimitError as e:
            print("Rate limit exceeded. Waiting...")
            print(e)
            signal.alarm(0)
            time.sleep(5)
        except openai._exceptions.APIConnectionError as e:
            print("API connection error. Waiting...")
            signal.alarm(0)
            time.sleep(5)
        except Exception as e:
            print("Unknown error. Waiting...")
            print(e)
            signal.alarm(0)
            time.sleep(1)
    return ret

def handler(signum, frame):
    # swallow signum and frame
    raise Exception("end of time")



class LocalizeFiles:
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

    def _parse_model_return_lines(self, content: str) -> List[str]:
        return content.strip().split("\n")

    def localize_files(self, problem_statement: str, top_n: int, repo_dir: str) -> Tuple[List[str], Dict[str, Any], Dict[str, Any]]:
        structure = create_structure(repo_dir)
        filter_none_python(structure)

        found_files = []
        message = self.obtain_relevant_files_prompt.format(
            problem_statement=problem_statement,
            structure=show_project_structure(structure),
        )

        config = create_chatgpt_config(
            message=message,
            max_tokens=self.max_tokens,
            temperature=0,
            batch_size=1,
            model="gpt-4o-2024-05-13",
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
        
        files, _, _ = get_full_file_paths_and_classes_and_functions(structure)
        file_contents = [f[0] for f in files]

        for file in model_found_files:
            if file in file_contents:
                found_files.append(file)

        found_files = sorted(found_files, key=lambda x: model_found_files.index(x))

        return (
            found_files,
            {"raw_output_files": raw_output},
            traj,
        )

def main():
    if len(sys.argv) != 4:
        print("Usage: python _localize_file.py <problem_statement> <repo_dir> <top_n>")
        sys.exit(1)

    problem_statement = sys.argv[1]
    repo_dir = sys.argv[2]
    top_n = int(sys.argv[3])

    LF = LocalizeFiles()
    found_files, additional_artifact_loc_file, file_traj = LF.localize_files(problem_statement, top_n, repo_dir)
    
    # output = {
    #     "found_files": found_files,
    #     "additional_artifact": additional_artifact_loc_file,
    #     "trajectory": file_traj
    # }
    print("Found files:")
    for file in found_files:
        print(file)
    
    # print(f"<<COMMAND_OUTPUT>>{json.dumps(output)}<<COMMAND_OUTPUT>>")

if __name__ == "__main__":
    main()