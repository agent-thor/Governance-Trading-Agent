from langchain_community.llms import Ollama
import pandas as pd
import os

class Summarization:
    def __init__(self, model):
        self.model = model
    
    def summarize_text(self, description):
        llm = Ollama(model=self.model, temperature=0.3)
        if len(description.split(' ')) >= 100:
            prompt = f"summarize the sentiment of following text. remove any integer value or web page link and any other noise and limit the output in between 30-60 words: {description}"
        
        if len(description.split(' ')) < 100:
            prompt = f"summarize the sentiment of following text. remove any integer value or web page link and any other noise and limit the output in between 10-20 words: {description}"

        
        output = llm.invoke(prompt)
        
        return output
    

