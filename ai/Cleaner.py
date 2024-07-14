import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from autocorrect import Speller

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('wordnet')

# Initialize the spell checker and lemmatizer
spell = Speller(lang='en')
lemm = WordNetLemmatizer()

# Function to reduce lengthening of words
def reduce_lengthening(text):
    pattern = re.compile(r"(.)\1{2,}")
    return pattern.sub(r"\1\1", text)

# Function to preprocess the text
def text_preprocess(doc):
    # Lowercase the text
    temp = doc.lower()
    
    # Remove specific XML characters
    temp = re.sub(r"&(?:apos|quot);", "", temp)
    
    # Remove hashtags, mentions, special characters, stock tickers, numbers, and single quotes
    temp = re.sub(r"[@#\$~+%=/-]", "", temp)
    temp = re.sub(r"[0-9]", "", temp)
    temp = re.sub(r"'", " ", temp)

    # Tokenize, truncate, and pad the text
    temp = word_tokenize(temp)
    temp = temp[:669] + [''] * (669 - len(temp)) if len(temp) < 669 else temp[:669]

    # Apply the spell checker, lemmatizer, and remove short words
    temp = [lemm.lemmatize(spell(reduce_lengthening(w))) for w in temp if len(w) > 2]

    return " ".join(temp)

# Function to remove URLs using regex
def remove_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub('', text)

# Function to remove emojis using regex
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

# Function to clean data
def clean_data(url, rows, comments=False):
    df = pd.read_csv(url, nrows=rows)
    
    # Remove rows containing 'referral' in the text
    df = df[~df['Text'].str.contains('referral', case=False, na=False)]
    
    # Apply URL and emoji removal, then preprocess the text
    df['clean_body'] = df['Text'].apply(remove_urls).apply(remove_emojis).apply(text_preprocess)
    
    # Remove rows with empty bodies
    df_cleaned = df[df['clean_body'].str.strip().astype(bool)]
    print("Finished cleaning")
    
    if comments:
        result_df = df[['Post_ID', 'Date_Published', 'Company', 'Comment_ID', 'clean_body']]
        # For now, save the cleaned comment data to a CSV file for visualization
        result_df.to_csv("../data/cleaned_comment_data.csv", index=False)
    else:
        result_df = df_cleaned[['Post_ID', 'Date_Published', 'Company', 'clean_body', 'Like_Count', 'View_Count' ]]
        # Save the cleaned post data to a CSV file for visualization
        result_df.to_csv("../data/cleaned_post_data.csv", index=False)
    
    return result_df
