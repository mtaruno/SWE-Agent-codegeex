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
    local localize_script="${SWE_LOCALIZE_SCRIPT:-/sweagent/config/commands/_localize_file.py}"
    
    # Debug: Show all all the current commands
    echo "Current commands:" >&2
    ls -1 /root/commands/ >&2
    echo "---" >&2
    
    # Debug: Print current working directory
    echo "Current working directory: $(pwd)" >&2

    # Debug: List contents of /sweagent/config/commands/
    echo "Contents of /sweagent/config/commands/:" >&2
    ls -la /sweagent/config/commands/ >&2

    # Debug: Print the value of SWE_LOCALIZE_SCRIPT
    echo "SWE_LOCALIZE_SCRIPT: $SWE_LOCALIZE_SCRIPT" >&2

    if [ ! -f "$localize_script" ]; then
        echo "Error: _localize_file.py not found at $localize_script" >&2
        # Debug: Try to find the file
        echo "Searching for _localize_file.py:" >&2
        find / -name "_localize_file.py" 2>/dev/null >&2
        return 1
    fi

    echo "Using _localize_file.py from: $localize_script" >&2

    # Debug: Check if the script is executable
    if [ -x "$localize_script" ]; then
        echo "The script is executable" >&2
    else
        echo "The script is not executable" >&2
    fi

    # Run the Python script with the correct path
    result=$(python "$localize_script" "$issue_text" "$dir_path" "$top_n")
    echo "$result"
}
