from langchain_community.llms import Ollama
from openai import OpenAI, OpenAIError
import pandas as pd
import os
import json
import re
import time
from typing import Tuple, Optional
from dotenv import load_dotenv
import ast


load_dotenv()

class Reasoning:
    def __init__(self, openai_api_key):
        self.max_attempts = 5
        self.retry_delay = 1  # seconds between retries
        self.client = OpenAI(api_key=openai_api_key)
        self.ollama_weight = 0.4
        self.openai_weight = 0.5
        self.trained_weight = 0.1
    
    def get_sentiment_score(self, output: str) -> float:
        """
        Extract sentiment score from LLM output using regex pattern matching.
        """
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, output)
    
        for match in matches:
            try:
                # Parse the match as JSON
                data = json.loads(match)
                
                # Check if 'score' is in the parsed dictionary
                if 'score' in data:
                    score = float(data['score'])
                    # Validate that the score is between 0 and 1
                    if 0 <= score <= 1:
                        return score
            except json.JSONDecodeError:
                # If parsing fails, move to the next match
                continue
        
        raise ValueError("No valid sentiment score found in output")

    def get_openai_sentiment(self, description: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Get sentiment score from OpenAI model with retry logic.
        Returns a tuple of (sentiment, score) or (None, None) if the sentiment couldn't be retrieved.
        """
        initial_prompt = """
        You are a financial and trading expert. Based on the content of this text, evaluate its sentiment and immediate impact on market prices.
        Output your result in JSON format as {'positive': x} or {'negative': x}, where:
        - x represents the score that can be in between 0 to 1.
        Output only the JSON object.
        """
        description = description + initial_prompt
   
        for attempt in range(self.max_attempts):
            print(f"attempt {attempt}")
            try:
                response = self.client.chat.completions.create(
                    model="o1-preview",
                    messages = [
                         {"role": "user", "content": description}
                     ]
                )
                
                output = response.choices[0].message.content
                try:
                    # Parse JSON using regex and json library
                    json_match = re.search(r'\{[^{}]*\}', output)
                    if json_match:
                        json_str = json_match.group()
                        json_str_fixed = json_str.replace("'", '"')
                        result = json.loads(json_str_fixed)
                        sentiment, score = next(iter(result.items()))
                        
                        return sentiment, float(score)
                    else:
                        if attempt == self.max_attempts - 1:
                            return None, None
                        time.sleep(self.retry_delay)
                        continue
                        
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    if attempt == self.max_attempts - 1:
                        return None, None
                    time.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                if attempt == self.max_attempts - 1:
                    return None, None
                time.sleep(self.retry_delay)
                continue
    
    def get_deepseek_sentiment(self, description: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Get sentiment score from Deepseek model with retry logic.
        Returns a tuple of (sentiment, score) or (None, None) if the sentiment couldn't be retrieved.
        """
        agent_endpoint = os.getenv("AGENT_ENDPOINT")
        agent_key = os.getenv("AGENT_KEY")
        
        client = OpenAI(
            base_url=agent_endpoint,
            api_key=agent_key,
        )
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            print(f"try {retry_count}")
            try:
                response = client.chat.completions.create(
                    model="n/a",
                    messages=[
                        {"role": "system", "content": """
                         You are a financial and trading expert. Based on the content of this text, evaluate its sentiment and immediate impact on market prices.
                         Output your result in JSON format as {'positive': x} or {'negative': x}, where:
                         - x represents the score that can be in between 0 to 1.
                         Output only the JSON object.
                         """},
                        {"role": "user", "content": description}
                    ]
                )
                
                for choice in response.choices:
                    content = choice.message.content
                    # Find JSON pattern between curly braces, including the braces
                    json_match = re.search(r'\{[^{}]*\}', content)
                    if json_match:
                        json_str = json_match.group()
                        json_str_fixed = json_str.replace("'", '"')
                        try:
                            result = json.loads(json_str_fixed)  # Parse JSON string to dict
                            sentiment, score = next(iter(result.items()))
                            return sentiment, float(score)
                        except json.JSONDecodeError:
                            # If first attempt fails, try with ast.literal_eval
                            try:
                                result = ast.literal_eval(json_str)
                                sentiment, score = next(iter(result.items()))
                                return sentiment, float(score)
                            except (ValueError, SyntaxError):
                                # Continue to next retry if both parsing methods fail
                                pass
                
                # If we didn't find JSON in the response, increment retry counter
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)  # Add a small delay between retries
                    continue
                else:
                    return None, None
                    
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    return None, None
                time.sleep(1)  # Add a small delay between retries
                continue


    def calculate_weighted_sentiment(self, ollama_score: Optional[float], openai_score: Optional[float], trained_score: float) -> float:
        """
        Calculate weighted sentiment score combining both models.
        Adjusts weights if some scores are missing.
        """
        # If trained_score is the only score available
        if ollama_score is None and openai_score is None:
            return trained_score
            
        # If ollama_score is missing but openai_score is available
        elif ollama_score is None and openai_score is not None:
            # Redistribute ollama weight to openai and trained
            new_openai_weight = self.openai_weight + (self.ollama_weight * 0.6)
            new_trained_weight = self.trained_weight + (self.ollama_weight * 0.4)
            return (openai_score * new_openai_weight) + (trained_score * new_trained_weight)
            
        # If openai_score is missing but ollama_score is available
        elif openai_score is None and ollama_score is not None:
            # Redistribute openai weight to ollama and trained
            new_ollama_weight = self.ollama_weight + (self.openai_weight * 0.6)
            new_trained_weight = self.trained_weight + (self.openai_weight * 0.4)
            return (ollama_score * new_ollama_weight) + (trained_score * new_trained_weight)
            
        # If all scores are available
        else:
            return (ollama_score * self.ollama_weight) + (openai_score * self.openai_weight) + (trained_score * self.trained_weight)
    
    def predict_sentiment(self, description: str, trained_score: float) -> Tuple[Optional[str], float]:
        """
        Predict market sentiment from text description using both models.
        Handles cases where either model might fail to produce a score.
        """
        # Get deepseek sentiment score
        deepseek_sentiment, deepseek_score = self.get_deepseek_sentiment(description)
        print(f"Deepseek sentiment: {deepseek_sentiment}, score: {deepseek_score}")
               
        # Get OpenAI sentiment score
        openai_sentiment, openai_score = self.get_openai_sentiment(description)
        print(f"OpenAI sentiment: {openai_sentiment}, score: {openai_score}")
        print(f"Trained score: {trained_score}")
    
        # Determine final sentiment
        final_sentiment = None
        if deepseek_sentiment is not None:
            final_sentiment = deepseek_sentiment
        if openai_sentiment is not None:
            final_sentiment = openai_sentiment
        
        # Calculate weighted score based on available scores
        weighted_score = self.calculate_weighted_sentiment(
            deepseek_score,
            openai_score,
            trained_score
        )
            
        return final_sentiment, weighted_score
