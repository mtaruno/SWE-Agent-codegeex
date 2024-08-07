
import openai
import os
from api import query_gpt4

def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def chunk_text(text, max_chunk_size=2048):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def generate_latex_for_chunk(chunk):

    system_prompt = "You are a LaTeX expert for Tsinghua LaTeX. Please generate a LaTeX code for the following text chunk, only output the LaTeX. "
    messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                }, {
                    "role": "user",
                    "content": chunk,
                }
            ]

    response = query_gpt4(messages, model = "gpt-4", max_tokens=2048)
    return response

def combine_latex(chunks):
    header = r"""
\documentclass[UTF8]{ctexart}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{geometry}
\geometry{a4paper,scale=0.8}
\title{Your Title Here}
\author{Your Name Here}
\date{\today}
\begin{document}
\maketitle
"""

    footer = r"""
\end{document}
"""

    return header + '\n'.join(chunks) + footer

def save_latex_file(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main(input_file, output_file):
    text = read_text_file(input_file)
    chunks = chunk_text(text)
    latex_chunks = [generate_latex_for_chunk(chunk) for chunk in chunks]
    final_latex = combine_latex(latex_chunks)
    save_latex_file(final_latex, output_file)
    print(f"LaTeX file saved to {output_file}")

if __name__ == "__main__":
    input_file = 'data/thesis/report.txt'
    output_file = 'data/thesis/output.tex'
    main(input_file, output_file)