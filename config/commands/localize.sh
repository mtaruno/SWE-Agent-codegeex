# @yaml
# signature: find_sus_files <issue_text> [<dir_path>] <top_n>
# docstring: Find the top N most suspicious files given the issue text (and repository structure) that likely will contain the buggy location.
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
    local issue_text="$1"
    local dir_path="${2:-.}"  # Use current directory if not provided
    local top_n="$3"

    # Use the environment variable if set, otherwise use a default path
    # local localize_script="${SWE_LOCALIZE_SCRIPT:-/sweagent/config/commands/_localize_file.py}"
    # if [ ! -f "/root/commands/_localize_file.py" ]; then
    #     echo "Error: _localize_file.py not found in /root/commands." >&2
    #     return 1
    # fi
    localize_script="/root/commands/_localize_file.py"
    echo "Current directory contents:" >&2
    ls -R /root/commands >&2

    echo "Using _localize_file.py from: $localize_script" >&2
    echo "Contents of _localize_file.py:" >&2
    cat "$localize_script" >&2

    result=$(python "$localize_script" "$issue_text" "$dir_path" "$top_n")
    
    echo "$result"
}
