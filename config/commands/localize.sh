# @yaml
# signature: find_sus_files <issue_text> [<dir_path>] <top_n>
# docstring: Find the top 5 most suspicious files given the issue text (and repository structure) that likely will contain the buggy location.
# arguments:
#   issue_text:
#       type: string
#       description: the model will decide what these keywords are from the state, observation, or simply issue text provided and provide it as words separated by spaces.
#       required: true   
#   dir_path:
#       type: string
#       description: the directory to search in (if not provided, searches in the current directory)
#       required: false
#   top_n: 
#       type: int
#       description: the number of suspicious files to return
#       required: true
find_sus_files() {
# Example usage:
# python config/commands/_localize_file.py "Given a list of 5 relevant files, please find a way to implement a new command to this agent to localize to the relevant buggy location to implement a function to find a list of suspicious functions and classes that might warrant us modifying that part of the codebase." "/Users/matthewtaruno/Library/Mobile Documents/com~apple~CloudDocs/Dev/tree-agent" 5   
# Make the version that is related to the yaml arguments above but with shell
    output = $(python config/commands/_localize_file.py "$1" "$2" "$3")
    echo $output
}
