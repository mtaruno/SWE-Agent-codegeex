# @yaml
# signature: find_sus_files <issue_text> [<dir>]
# docstring: Find the top 5 most suspicious files given the issue text (and repository structure) that likely will contain the buggy location.
# arguments:
#   keywords:
#       type: string
#       description: the model will decide what these keywords are from the state, observation, or simply issue text provided and provide it as words separated by spaces.
#       required: true   
#   dir:
#       type: string
#       description: the directory to search in (if not provided, searches in the current directory)
#       required: false
find_sus_files() {
    
}


# @yaml
# signature: find_class_func <sus_files> [<dir>]
# docstring: Given suspicious files and file skeleton, we find the top n suspicious functions and classes
# arguments:
#   sus_files:
#       type: string
#       description: the model will decide what these keywords are from the state, observation, or simply issue text provided and provide it as words separated by spaces.
#       required: true   
#   dir:
#       type: string
#       description: the directory to search in (if not provided, searches in the current directory)
#       required: false
find_class_func() {

}


# @yaml
# signature: find_class_func <sus_snippets> [<dir>]
# docstring: Find the top 5 most suspicious files given the issue text
# arguments:
#   keywords:
#       type: string
#       description: the model will decide what these keywords are from the state, observation, or simply issue text provided and provide it as words separated by spaces.
#       required: true   
#   dir:
#       type: string
#       description: the directory to search in (if not provided, searches in the current directory)
#       required: false
find_lines() {

}

