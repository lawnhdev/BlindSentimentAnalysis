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
    temp = re.sub("&quot;", "",temp)
    #Removing hashtags, dollar signs and mentions
    temp = re.sub("@[A-Za-z0-9_]+","", temp)
    temp = re.sub("#[A-Za-z0-9_]+","", temp)
    temp = re.sub("[~+%=/-]", "", temp)
    # Removing stock tickers
    temp = re.sub("\$[A-Za-z]+", "", temp)
    #removing numbers
    temp = re.sub("[0-9]","", temp)
    #Removing '
    temp = re.sub("'"," ",temp)

    #Tokenization
    temp = word_tokenize(temp)
    temp = temp[:669]  # Truncate if longer
    if len(temp) < 669:
        temp += [''] * (669 - len(temp))  # Pad if shorter
    
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

def clean_data(url, rows, comments=False):
    df = pd.read_csv(url, nrows=rows)
    # remove the rows with referral in the text
    df = df[~df['Text'].str.contains('referral', case=False, na=False)]

    # apply the regex filter
    df['clean_body'] = df['Text'].apply(remove_urls).apply(remove_emojis).apply(text_preprocess)

    # remove rows with empty body
    df_cleaned = df[df['clean_body'].str.strip().astype(bool)]
    print("finished cleaning")
    
    if comments:
        #TODO uncomment  when I have new dataset with Company data 
        print(df)
        result_df = df[['Post_ID', 'Date_Published', 'Company', 'Comment_ID', 'clean_body']] 
        
        # result_df = df_cleaned[['Post_ID', 'Date_Published', 'Comment_ID', 'clean_body']] 
        # save the cleaned data to a csv file just for visualization 
        # this will be removed in the final implementation
        result_df.to_csv("../data/cleaned_comment_data.csv", index=False)
    else:
        result_df = df_cleaned[['Post_ID', 'Date_Published', 'Company', 'clean_body']] 
        # save the cleaned data to a csv file just for visualization 
        # this will be removed in the final implementation
        result_df.to_csv("../data/cleaned_post_data.csv", index=False)
    
    return result_df

