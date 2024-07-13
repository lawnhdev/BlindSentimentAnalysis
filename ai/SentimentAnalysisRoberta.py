from transformers import AutoModelForSequenceClassification
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoConfig
import numpy as np
import pandas as pd
import pprint
from scipy.special import softmax
from Cleaner import clean_post_data
from transformers import logging
import ImportCSVAll 
import argparse
import ImportCSV
import sqlite3
import datetime
logging.set_verbosity_error()

dataset_path = "../data/Post.csv"

MODEL = f"cardiffnlp/twitter-roberta-base-sentiment-latest"

# Analyzes a specific text body
def analyze_text(text):
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    encoded_input = tokenizer(text, return_tensors='pt')
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)

    return scores

#input a csv path
#cleans the data and analyzes each row assigning it 3 sentiment scores
#saves the scores to a csv file
def analyze_dataset(path):
    cleaned_data = clean_post_data(path, 1000)
    config = AutoConfig.from_pretrained(MODEL)

    data_list = []
    for idx, data in cleaned_data.iterrows():
        print("Analyzing post", idx)
        scores = analyze_text(data["clean_body"])
        ranking = np.argsort(scores)
        ranking = ranking[::-1]
        #change to post_id instead of body in final implementation 
        data_list.append({
            "company": data["Company"],
            "body": data["clean_body"], 
            "neutral": scores[ranking[0]],
            "positive": scores[ranking[1]],
            "negative": scores[ranking[2]]
        })

    pprint.pp(data_list)

    
    df = pd.DataFrame(data_list)
    # just writing to csv for now to see the data
    df.to_csv("../data/sentiment_scores.csv", index=False)
    return df



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate sentiment for a company")
    parser.add_argument("company", nargs='?', help="Company to generate for all history", type=str)
    args = parser.parse_args()
    if args.company == None:
        ImportCSVAll.write_to_csv()
    else:
        ImportCSV.write_to_csv_single(args.company)
    df = analyze_dataset(dataset_path)
    # group by company and get the average sentiment scores 
    #TODO use a weighted average when we have likes, comments, and views
    averages_df = df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()
    now = datetime.datetime.now()
    averages_df['date_computed'] = str(now)
    # replace with writing to the db
    conn = sqlite3.connect('../blind_posts.db')
    # cursor = conn.cursor()
    # cursor.execute('''CREATE TABLE IF NOT EXISTS Sentiment (
    #             Comment_ID INTEGER PRIMARY KEY,
    #             Company TEXT,
    #             Neutral REAL,
    #             Positive REAL,
    #             Negative REAL,
    #             Date_Published TEXT,
    #         )''')
    averages_df.to_sql('sentiment_scores', conn, if_exists='append')
    # cursor.execute('''INSERT INTO Sentiment (Company, Neutral, Positve, Negative, Date_Published )
    #             VALUES (?, ?, ?, ?, ?, ?, ?)''', averages_df)
    
    pprint.pp(averages_df)
        



    