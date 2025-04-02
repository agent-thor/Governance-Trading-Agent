import nltk
nltk.download('punkt')
nltk.download('words')


from nltk.corpus import words
from nltk.tokenize import word_tokenize
import string

# Load set of English words
english_words = set(words.words())

def text_validity_check(text):
    tokens = word_tokenize(text)
    tokens = [token.lower() for token in tokens if token not in string.punctuation]
    valid_words = sum(1 for token in tokens if token in english_words)
    
    if len(tokens) == 0:
        return 0  # Avoid division by zero
    proportion_of_valid_words = valid_words / len(tokens)
    
    return proportion_of_valid_words

def classify_text(text):
    threshold=0.5
    validity_score = text_validity_check(text)
    
    return "genuine" if validity_score > threshold else "not_genuine"
