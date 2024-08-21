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

class Agentless: 

    def __init__(self, problem_statement): 
        # problem statement is given by the LLM as "issue_text"
        self.problem_statement = problem_statement
        self.structure = create_structure(".")


    def localize_files(self):

        # get structure
        filter_none_python(self.structure)
        # filter_out_test_files(structure) #NOTE: should only do this for non pytest files

        found_files = []
        additional_artifact_loc_file = None
        file_traj = {}

        fl = LLMFL(
            self.structure,
            self.problem_statement,
        )
        found_files, additional_artifact_loc_file, file_traj = fl.localize()

    def localize_class_func(self, suspicious_files): 
        related_loc_traj = {}
        additional_artifact_loc_related = None

        # related class, functions, global var localization
        found_related_locs = []


        structure = None 

        if len(suspicious_files) != 0:
            pred_files = suspicious_files[: args.top_n]
            fl = LLMFL(
                structure,
                problem_statement,
            )

            additional_artifact_loc_related = []
            found_related_locs = []
            related_loc_traj = {}

            if args.compress:
                (
                    found_related_locs,
                    additional_artifact_loc_related,
                    related_loc_traj,
                ) = fl.localize_function_from_compressed_files(
                    pred_files,
                    mock=args.mock,
                )
                additional_artifact_loc_related = [additional_artifact_loc_related]
            else:
                assert False, "Not implemented yet."

    def localize_lines(self, suspicious_files, top_n, found_related_locs):

        edit_loc_traj = {}
        additional_artifact_loc_edit_location = None


        # Only supports the following args for now
        found_edit_locs = []
        pred_files = found_files[:top_n]
        fl = LLMFL(
            instance_id,
            structure,
            problem_statement,
        )
        coarse_found_locs = {}
        for i, pred_file in enumerate(pred_files):
            if len(found_related_locs) > i:
                coarse_found_locs[pred_file] = found_related_locs[i]
        (
            found_edit_locs,
            additional_artifact_loc_edit_location,
            edit_loc_traj,
        ) = fl.localize_line_from_coarse_function_locs(
            pred_files,
            coarse_found_locs,
            context_window=args.context_window,
            add_space=args.add_space,
            no_line_number=args.no_line_number,
            sticky_scroll=args.sticky_scroll,
            mock=args.mock,
            temperature=args.temperature,
            num_samples=args.num_samples,
        )

        additional_artifact_loc_edit_location = [
            additional_artifact_loc_edit_location
        ]
    


def construct_topn_file_context(
    file_to_locs,
    pred_files,
    file_contents,
    structure,
    context_window: int,
    loc_interval: bool = True,
    fine_grain_loc_only: bool = False,
    add_space: bool = False,
    sticky_scroll: bool = False,
    no_line_number: bool = True,
):
    """Concatenate provided locations to form a context.

    loc: {"file_name_1": ["loc_str_1"], ...}
    """
    file_loc_intervals = dict()
    topn_content = ""

    for pred_file, locs in file_to_locs.items():
        content = file_contents[pred_file]
        line_locs, context_intervals = transfer_arb_locs_to_locs(
            locs,
            structure,
            pred_file,
            context_window,
            loc_interval,
            fine_grain_loc_only,
            file_content=file_contents[pred_file] if pred_file in file_contents else "",
        )

        if len(line_locs) > 0:
            # Note that if no location is predicted, we exclude this file.
            file_loc_content = line_wrap_content(
                content,
                context_intervals,
                add_space=add_space,
                no_line_number=no_line_number,
                sticky_scroll=sticky_scroll,
            )
            topn_content += f"### {pred_file}\n{file_loc_content}\n\n\n"
            file_loc_intervals[pred_file] = context_intervals

    return topn_content, file_loc_intervals



class FL(ABC):
    def __init__(self, instance_id, structure, problem_statement):
        self.structure = structure
        self.problem_statement = problem_statement

    @abstractmethod
    def localize(self, top_n=1, mock=False) -> tuple[list, list, list, any]:
        pass


class LLMFL(FL):
    """This class does LLM File Localization"""
  

    obtain_relevant_code_prompt = """
Please look through the following GitHub problem description and file and provide a set of locations that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### File: {file_name} ###
{file_content}

###

Please provide either the class, the function name or line numbers that need to be edited.
### Example 1:
```
class: MyClass
```
### Example 2:
```
function: my_function
```
### Example 3:
```
line: 10
line: 24
```

Return just the location(s)
"""
    file_content_template = """
### File: {file_name} ###
{file_content}
"""
    file_content_in_block_template = """
### File: {file_name} ###
```python
{file_content}
```
"""
    obtain_relevant_code_combine_top_n_prompt = """
Please review the following GitHub problem description and relevant files, and provide a set of locations that need to be edited to fix the issue.
The locations can be specified as class names, function or method names, or exact line numbers that require modification.

### GitHub Problem Description ###
{problem_statement}

###
{file_contents}

###

Please provide the class name, function or method name, or the exact line numbers that need to be edited.
### Examples:
```
full_path1/file1.py
line: 10
class: MyClass1
line: 51

full_path2/file2.py
function: MyClass2.my_method
line: 12

full_path3/file3.py
function: my_function
line: 24
line: 156
```

Return just the location(s)
"""
    obtain_relevant_code_combine_top_n_no_line_number_prompt = """
Please review the following GitHub problem description and relevant files, and provide a set of locations that need to be edited to fix the issue.
The locations can be specified as class, method, or function names that require modification.

### GitHub Problem Description ###
{problem_statement}

###
{file_contents}

###

Please provide the class, method, or function names that need to be edited.
### Examples:
```
full_path1/file1.py
function: my_function1
class: MyClass1

full_path2/file2.py
function: MyClass2.my_method
class: MyClass3

full_path3/file3.py
function: my_function2
```

Return just the location(s)
"""
    obtain_relevant_functions_from_compressed_files_prompt = """
Please look through the following GitHub problem description and the skeleton of relevant files.
Provide a thorough set of locations that need inspection or editing to fix the problem, including directly related areas as well as any potentially related functions and classes.

### GitHub Problem Description ###
{problem_statement}

###
{file_contents}

###

Please provide locations as either the class or the function name.
### Examples:
```
full_path1/file1.py
class: MyClass1

full_path2/file2.py
function: MyClass2.my_method

full_path3/file3.py
function: my_function
```

Return just the location(s)
"""
    obtain_relevant_functions_and_vars_from_compressed_files_prompt_more = """
Please look through the following GitHub Problem Description and the Skeleton of Relevant Files.
Identify all locations that need inspection or editing to fix the problem, including directly related areas as well as any potentially related global variables, functions, and classes.
For each location you provide, either give the name of the class, the name of a method in a class, the name of a function, or the name of a global variable.

### GitHub Problem Description ###
{problem_statement}

### Skeleton of Relevant Files ###
{file_contents}

###

Please provide the complete set of locations as either a class name, a function name, or a variable name.
Note that if you include a class, you do not need to list its specific methods.
You can include either the entire class or don't include the class name and instead include specific methods in the class.
### Examples:
```
full_path1/file1.py
function: my_function_1
class: MyClass1
function: MyClass2.my_method

full_path2/file2.py
variable: my_var
function: MyClass3.my_method

full_path3/file3.py
function: my_function_2
function: my_function_3
function: MyClass4.my_method_1
class: MyClass5
```

Return just the locations.
"""
    def __init__(self, instance_id, structure, problem_statement, **kwargs):
        self.max_tokens = 300

    def _parse_model_return_lines(self, content: str) -> list[str]:
        return content.strip().split("\n")

    def localize(self, top_n=1, mock=False) -> tuple[list, list, list, any]:

        found_files = []

        # lazy import, not sure if this is actually better?
        from util.api_requests import (
            create_chatgpt_config,
            num_tokens_from_messages,
            request_chatgpt_engine,
        )

        message = self.obtain_relevant_files_prompt.format(
            problem_statement=self.problem_statement,
            structure=show_project_structure(self.structure).strip(),
        ).strip()

        print(f"prompting with message:\n{message}")
        print("=" * 80)
        if mock:
            traj = {
                "prompt": message,
                "usage": {
                    "prompt_tokens": num_tokens_from_messages(
                        message, "gpt-4o-2024-05-13"
                    ),
                },
            }
            return [], {"raw_output_loc": ""}, traj

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
            self.structure
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

    def localize_function_for_files(
        self, file_names, mock=False
    ) -> tuple[list, dict, dict]:
        from util.api_requests import (
            create_chatgpt_config,
            num_tokens_from_messages,
            request_chatgpt_engine,
        )

        files, classes, functions = get_full_file_paths_and_classes_and_functions(
            self.structure
        )

        max_num_files = len(file_names)
        while 1:
            # added small fix to prevent too many tokens
            contents = []
            for file_name in file_names[:max_num_files]:
                for file_content in files:
                    if file_content[0] == file_name:
                        content = "\n".join(file_content[1])
                        file_content = line_wrap_content(content)
                        contents.append(
                            self.file_content_template.format(
                                file_name=file_name, file_content=file_content
                            )
                        )
                        break
                else:
                    raise ValueError(f"File {file_name} does not exist.")

            file_contents = "".join(contents)
            if num_tokens_from_messages(file_contents, "gpt-4o-2024-05-13") < 128000:
                break
            else:
                max_num_files -= 1

        message = self.obtain_relevant_code_combine_top_n_prompt.format(
            problem_statement=self.problem_statement,
            file_contents=file_contents,
        ).strip()
        print(f"prompting with message:\n{message}")
        print("=" * 80)
        if mock:
            traj = {
                "prompt": message,
                "usage": {
                    "prompt_tokens": num_tokens_from_messages(
                        message, "gpt-4o-2024-05-13"
                    ),
                },
            }
            return [], {"raw_output_loc": ""}, traj

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

        model_found_locs = extract_code_blocks(raw_output)
        model_found_locs_separated = extract_locs_for_files(
            model_found_locs, file_names
        )

        print(raw_output)

        return model_found_locs_separated, {"raw_output_loc": raw_output}, traj

    def localize_function_from_compressed_files(self, file_names, mock=False):
        from util.api_requests import (
            create_chatgpt_config,
            num_tokens_from_messages,
            request_chatgpt_engine,
        )

        file_contents = get_repo_files(self.structure, file_names)
        compressed_file_contents = {
            fn: get_skeleton(code) for fn, code in file_contents.items()
        }
        contents = [
            self.file_content_in_block_template.format(file_name=fn, file_content=code)
            for fn, code in compressed_file_contents.items()
        ]
        file_contents = "".join(contents)
        template = (
            self.obtain_relevant_functions_and_vars_from_compressed_files_prompt_more
        )
        message = template.format(
            problem_statement=self.problem_statement, file_contents=file_contents
        )
        assert num_tokens_from_messages(message, "gpt-4o-2024-05-13") < 128000
        logging.info(f"prompting with message:\n{message}")
        logging.info("=" * 80)

        if mock:
            traj = {
                "prompt": message,
                "usage": {
                    "prompt_tokens": num_tokens_from_messages(
                        message, "gpt-4o-2024-05-13"
                    ),
                },
            }
            return [], {"raw_output_loc": ""}, traj

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

        model_found_locs = extract_code_blocks(raw_output)
        model_found_locs_separated = extract_locs_for_files(
            model_found_locs, file_names
        )

        logging.info(f"==== raw output ====")
        logging.info(raw_output)
        logging.info("=" * 80)
        logging.info(f"==== extracted locs ====")
        for loc in model_found_locs_separated:
            logging.info(loc)
        logging.info("=" * 80)

        return model_found_locs_separated, {"raw_output_loc": raw_output}, traj

    def localize_line_from_coarse_function_locs(
        self,
        file_names,
        coarse_locs,
        context_window: int,
        add_space: bool,
        sticky_scroll: bool,
        no_line_number: bool,
        temperature: float = 0.0,
        num_samples: int = 1,
        mock=False,
    ):
        from util.api_requests import (
            create_chatgpt_config,
            num_tokens_from_messages,
            request_chatgpt_engine,
        )

        file_contents = get_repo_files(self.structure, file_names)
        topn_content, file_loc_intervals = construct_topn_file_context(
            coarse_locs,
            file_names,
            file_contents,
            self.structure,
            context_window=context_window,
            loc_interval=True,
            add_space=add_space,
            sticky_scroll=sticky_scroll,
            no_line_number=no_line_number,
        )
        if no_line_number:
            template = self.obtain_relevant_code_combine_top_n_no_line_number_prompt
        else:
            template = self.obtain_relevant_code_combine_top_n_prompt
        message = template.format(
            problem_statement=self.problem_statement, file_contents=topn_content
        )
        logging.info(f"prompting with message:\n{message}")
        logging.info("=" * 80)
        assert num_tokens_from_messages(message, "gpt-4o-2024-05-13") < 128000
        if mock:
            traj = {
                "prompt": message,
                "usage": {
                    "prompt_tokens": num_tokens_from_messages(
                        message, "gpt-4o-2024-05-13"
                    ),
                },
            }
            return [], {"raw_output_loc": ""}, traj
        config = create_chatgpt_config(
            message=message,
            max_tokens=self.max_tokens,
            temperature=temperature,
            batch_size=num_samples,
            model="gpt-4o-2024-05-13",  # use gpt-4o for now.
        )
        ret = request_chatgpt_engine(config)
        raw_outputs = [choice.message.content for choice in ret.choices]
        traj = {
            "prompt": message,
            "response": raw_outputs,
            "usage": {
                "prompt_tokens": ret.usage.prompt_tokens,
                "completion_tokens": ret.usage.completion_tokens,
            },
        }
        model_found_locs_separated_in_samples = []
        for raw_output in raw_outputs:
            model_found_locs = extract_code_blocks(raw_output)
            model_found_locs_separated = extract_locs_for_files(
                model_found_locs, file_names
            )
            model_found_locs_separated_in_samples.append(model_found_locs_separated)

            logging.info(f"==== raw output ====")
            logging.info(raw_output)
            logging.info("=" * 80)
            print(raw_output)
            print("=" * 80)
            logging.info(f"==== extracted locs ====")
            for loc in model_found_locs_separated:
                logging.info(loc)
            logging.info("=" * 80)
        logging.info("==== Input coarse_locs")
        coarse_info = ""
        for fn, found_locs in coarse_locs.items():
            coarse_info += f"### {fn}\n"
            if isinstance(found_locs, str):
                coarse_info += found_locs + "\n"
            else:
                coarse_info += "\n".join(found_locs) + "\n"
        logging.info("\n" + coarse_info)
        if len(model_found_locs_separated_in_samples) == 1:
            model_found_locs_separated_in_samples = (
                model_found_locs_separated_in_samples[0]
            )

        return (
            model_found_locs_separated_in_samples,
            {"raw_output_loc": raw_outputs},
            traj,
        )
    

    