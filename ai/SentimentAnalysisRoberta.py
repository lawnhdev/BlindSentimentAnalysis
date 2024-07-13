from transformers import AutoModelForSequenceClassification
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoConfig
import numpy as np
import pandas as pd
import pprint
from scipy.special import softmax
from Cleaner import clean_data
from transformers import logging
import ImportCSVAll 
import argparse
import ImportCSV
import sqlite3
import datetime
logging.set_verbosity_error()

post_dataset_path = "../data/Post.csv"

comments_dataset_path = "../data/Comment.csv"
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
    cleaned_data = clean_data(path, 1000)
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

    #pprint.pp(data_list)
    df = pd.DataFrame(data_list)
    # just writing to csv for now to see the data
    df.to_csv("../data/sentiment_scores.csv", index=False)
    return df

def analyze_post_comments(post_id, comment_data):
    filtered_comments = comment_data.loc[comment_data['Post_ID'] == post_id]
    comment_scores = []
    #iterate through the comments with a given post_id and calculate the scores of each comment
    for idx, data in filtered_comments.iterrows():
        print("Analyzing comments for post_id:", post_id)
        scores = analyze_text(data["clean_body"])
        ranking = np.argsort(scores)
        ranking = ranking[::-1]
        comment_scores.append({
            #"company": data["Company"], uncomment when I have new dataset with Company data
            "post_id": data["Post_ID"],
            "comment_id": data["Comment_ID"],
            "neutral": scores[ranking[0]],
            "positive": scores[ranking[1]],
            "negative": scores[ranking[2]]
        })
    #return the scores of the comments for a given post_id
    return pd.DataFrame(comment_scores)
    
    

#bool if we want the comments to be weighted the same as the post or if comments are weighted as a single entity
def analyze_dataset_with_comments(post_path, comments_path, weighted):
    cleaned_post_data = clean_data(post_path, 1000)
    #comments=True to save the correct data
    cleaned_comments_data = clean_data(comments_path, 1000, True)
    config = AutoConfig.from_pretrained(MODEL)

    data_list = []
    #assumes that a given post_id will only appear once in the post dataset
    for idx, data in cleaned_post_data.iterrows():
        print("Analyzing post", data["Post_ID"])
        #get the scores of the comments for a given post_id
        comment_scores = analyze_post_comments(data["Post_ID"], cleaned_comments_data)
        post_scores = analyze_text(data["clean_body"])
        post_scores_df = pd.DataFrame([post_scores], columns=['neutral', 'positive', 'negative'])
        if weighted:
            combined_scores = pd.concat([post_scores_df, comment_scores], ignore_index=True)
            # Calculate the average scores where each entry is weighted equally
            average_scores = combined_scores.mean()
            data_list.append({
                "company": data["Company"], 
                "post_id": data["Post_ID"], 
                "neutral": average_scores.iloc[0],
                "positive": average_scores.iloc[1],
                "negative": average_scores.iloc[2]
            })
        else:
            average_comment_scores = comment_scores.mean()
            # treat post scores and ALL comments as equal
            combined_average_scores = (post_scores_df.iloc[0] + average_comment_scores) / 2
            data_list.append({
                "company": data["Company"], 
                "post_id": data["Post_ID"], 
                "neutral": combined_average_scores['neutral'],
                "positive": combined_average_scores['positive'],
                "negative": combined_average_scores['negative']
            })


    #pprint.pp(data_list)
    df = pd.DataFrame(data_list)
    # just writing to csv for now to see the data
    if weighted:
        df.to_csv("../data/sentiment_scores_weighted_comments.csv", index=False)
    else:
        df.to_csv("../data/sentiment_scores_unweighted_comments.csv", index=False)
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
    # dataset with just posts
    post_df = analyze_dataset(post_dataset_path)
    #dataset with posts + comments weighted equally
    weighted_df = analyze_dataset_with_comments(post_dataset_path, comments_dataset_path, True)
    #dataset with posts + comments unweighted
    unweighted_df = analyze_dataset_with_comments(post_dataset_path, comments_dataset_path, False)


    #TODO use a weighted average for posts when we have likes and views

    #group by company and get the average sentiment scores with just posts 
    comp_avg_no_comments_df = post_df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()

    #group by company and get the average sentiment scores with posts and comments weighted equally
    comp_avg_weighted_df = weighted_df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()

    #group by company and get the average sentiment scores with posts and comments unweighted
    company_avg_unweighted_df = unweighted_df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()

    # replace with writing to the db
    print('no comments: ', comp_avg_no_comments_df)
    print('weighted comments: ', comp_avg_weighted_df)
    print('unweighted comments ', company_avg_unweighted_df)

        



    