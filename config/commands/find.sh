# @yaml
# signature: bm25 <keywords> [<dir>]
# docstring: Given keywords related to the issue text provided, we see an entire list of repository files and sort it by how related it is to the keywords, hoping that higher ranked documents are more likely to contain the buggy location.
# arguments:
#   keywords:
#       type: string
#       description: the model will decide what these keywords are from the state, observation, or simply issue text provided and provide it as words separated by spaces.
#       required: true   
#   dir:
#       type: string
#       description: the directory to search in (if not provided, searches in the current directory)
#       required: false
bm25() {
    # Ensure keywords are provided
    if [ -z "$1" ]; then
        echo "Usage: bm25 <keywords> [<dir>]"
        return
    fi

    # Assign keywords and directory
    local keywords="$1"
    local dir="${2:-./}"

    # Verify that the directory exists
    if [ ! -d "$dir" ]; then
        echo "Directory $dir not found"
        return
    fi

    # Convert the directory to an absolute path
    dir=$(realpath "$dir")

    # Function to calculate the BM25 score for a document
    calculate_bm25() {
        local doc_file="$1"
        local keyword_list=($keywords)
        local doc_length=$(wc -w < "$doc_file")
        local avg_doc_length=0
        local total_docs=0

        # Calculate total number of documents and average document length
        for file in $(find "$dir" -type f); do
            local file_length=$(wc -w < "$file")
            avg_doc_length=$((avg_doc_length + file_length))
            total_docs=$((total_docs + 1))
        done
        avg_doc_length=$((avg_doc_length / total_docs))

        # BM25 parameters
        local k1=1.5
        local b=0.75
        local bm25_score=0

        # Calculate BM25 for each keyword
        for keyword in "${keyword_list[@]}"; do
            local term_freq=$(grep -o "\b$keyword\b" "$doc_file" | wc -l)
            local doc_count=$(grep -lR "\b$keyword\b" "$dir" | wc -l)

            # Calculate Inverse Document Frequency (IDF)
            if [ $doc_count -eq 0 ]; then
                continue
            fi
            local idf=$(awk -v N=$total_docs -v df=$doc_count 'BEGIN { print log((N - df + 0.5) / (df + 0.5)) }')

            # Calculate term frequency weight
            local tf_weight=$(awk -v tf=$term_freq -v doc_len=$doc_length -v avg_len=$avg_doc_length -v k1=$k1 -v b=$b 'BEGIN { print ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_len)))) }')

            # Accumulate BM25 score
            bm25_score=$(awk -v score=$bm25_score -v idf=$idf -v tf_weight=$tf_weight 'BEGIN { print score + idf * tf_weight }')
        done

        echo "$bm25_score"
    }

    # Store BM25 scores and file paths
    declare -A file_scores

    # Iterate over files and calculate BM25 score
    for file in $(find "$dir" -type f); do
        local score=$(calculate_bm25 "$file")
        file_scores["$file"]=$score
    done

    # Sort files based on BM25 scores
    echo "Ranking files based on BM25 scores:"
    for file in "${!file_scores[@]}"; do
        echo "${file_scores[$file]} $file"
    done | sort -nr -k1

    echo "End of BM25 ranking"
}



# Execute the function with arguments passed to the script
bm25 "$@"