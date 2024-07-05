#!/bin/bash
python "/Users/matthewtaruno/Library/Mobile Documents/com~apple~CloudDocs/Dev/SWE-agent/run.py" \
    --model_name gpt-4-0125-preview \
    --data_path princeton-nlp/SWE-bench_Lite_oracle \
    --per_instance_cost_limit 3.00 \
    --config_file '/Users/matthewtaruno/Library/Mobile Documents/com~apple~CloudDocs/Dev/SWE-agent/config/default.yaml' \
    --skip_existing