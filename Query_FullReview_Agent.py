import streamlit as st
import os
from pypdf import PdfReader
import re
import requests
from model import *

def clean(text):
    indicator = 0
    if "REFERENCES\n[1]" in text:
        text = text + ' [EOP]'
        indicator = 1
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return (text, indicator)

def read_file(file):
    reader = PdfReader(file)
    file_text = ""

    for page in reader.pages:
        page_text, indicator = clean(page.extract_text())
        file_text = file_text + page_text
        if indicator == 1:
            break
        if len(file_text) > 1280:
            file_text = file_text[:1280]
            break

    return file_text


# Function to genrate the model response
def reply_on(paper_set, prompt):
    st.write(f"Analyzing {len(paper_set)} files..... Thinking.....")

    context = ""
    if isinstance(paper_set, str):
        max_response_length = 500
        context = read_file(paper_set)
    elif isinstance(paper_set, list):
        max_response_length = 500
        for paper in paper_set:
            context = context + read_file(paper)
    
    query_content = context + prompt
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Can you provide ways to eat combinations of bananas and dragonfruits?"},
        {"role": "assistant", "content": "Sure! Here are some ways to eat bananas and dragonfruits together: 1. Banana and dragonfruit smoothie: Blend bananas and dragonfruits together with some milk and honey. 2. Banana and dragonfruit salad: Mix sliced bananas and dragonfruits together with some lemon juice and honey."},
        {"role": "user", "content": query_content},
    ]
    
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
    
    generation_args = {
        "max_new_tokens": max_response_length,
        "return_full_text": False,
        "temperature": 0.0,
        "do_sample": False,
    }
    
    output = pipe(messages, **generation_args)
    reply = output[0]['generated_text']

    return reply

# Streamlit App Interface
def main():
    # App title
    st.title("Research Papers Analysis")

    # User Input Fields
    file_list = st.text_input("Enter Research file names:", "")
    user_prompt = st.text_input("Query:", "")

    # Interactive Run Analysis
    if st.button("Run Analysis"):
        if file_list and user_prompt:
            # Split the file_list into a list of filenames
            files = [file.strip() for file in file_list.split(',')]
            # Invoke the analysis function with the user inputs
            result = reply_on(files, user_prompt)
            st.write(f"Analysis : {result}")
        else:
            st.error("Please provide both file names and a query.")

    # print(result)

if __name__ == '__main__':
    main()
