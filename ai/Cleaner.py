import pandas as pd
import re 
import nltk

nltk.download('punkt')
nltk.download('wordnet')
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from autocorrect import Speller
spell = Speller(lang='en')
lemm = WordNetLemmatizer()

#Fixing Word Lengthening
def reduce_lengthening(text):
    pattern = re.compile(r"(.)\1{2,}")
    return pattern.sub(r"\1\1", text)

def text_preprocess(doc):
    #Lowercasing all the letters
    temp = doc.lower()
    
    #removing the XML apostrophe
    temp = re.sub("&apos;", "", temp)

    #Removing hashtags, dollar signs and mentions
    temp = re.sub("@[A-Za-z0-9_]+","", temp)
    temp = re.sub("#[A-Za-z0-9_]+","", temp)
    # temp = re.sub("[$%-]", "", temp)

    # Removing stock tickers
    temp = re.sub("\$[A-Za-z]+", "", temp)

    #removing numbers
    temp = re.sub("[0-9]","", temp)
    #Removing '
    temp = re.sub("'"," ",temp)

    #Tokenization
    temp = word_tokenize(temp)
    #Fixing Word Lengthening
    temp = [reduce_lengthening(w) for w in temp]
    #spell corrector
    temp = [spell(w) for w in temp]
    #stem
    temp = [lemm.lemmatize(w) for w in temp]
    #Removing short words
    temp = [w for w in temp if len(w)>2]

    temp = " ".join(w for w in temp)
    return temp

# Function to remove URLs using regex
def remove_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub('', text)

# Function to remove emojis using regex
def remove_emojis(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
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

def clean_data(url, rows):
    df = pd.read_csv(url, nrows=rows)
    df['clean_body'] = df['body'].apply(remove_urls).apply(remove_emojis).apply(text_preprocess)
    print("finished cleaning")
    result_df = df[['tweet_id', 'post_date', 'clean_body']]
    # result_df.to_csv("../data/cleaned_data.csv", index=False)
    return result_df
