from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
import numpy as np
import pandas as pd
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
MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Load model and tokenizer once
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
config = AutoConfig.from_pretrained(MODEL)

# Analyzes a specific text body
def analyze_text(text):
    encoded_input = tokenizer(text, return_tensors='pt')
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    return scores

def analyze_dataset(path, rows=1000):
    cleaned_data = clean_data(path, rows)
    data_list = []
    #iterate through the cleaned posts and calculate sentiment scores for each
    for idx, data in cleaned_data.iterrows():
        scores = analyze_text(data["clean_body"])
        ranking = np.argsort(scores)[::-1]
        data_list.append({
            "company": data["Company"],
            "body": data["clean_body"], 
            "neutral": scores[ranking[0]],
            "positive": scores[ranking[1]],
            "negative": scores[ranking[2]]
        })

    df = pd.DataFrame(data_list)
    df.to_csv("../data/sentiment_scores.csv", index=False)
    return df

def analyze_post_comments(post_id, comment_data):
    filtered_comments = comment_data.loc[comment_data['Post_ID'] == post_id]
    comment_scores = []

    #iterate through the comments and calculate sentiment scores for each
    for idx, data in filtered_comments.iterrows():
        scores = analyze_text(data["clean_body"])
        ranking = np.argsort(scores)[::-1]
        comment_scores.append({
            "company": data["Company"],
            "post_id": data["Post_ID"],
            "comment_id": data["Comment_ID"],
            "neutral": scores[ranking[0]],
            "positive": scores[ranking[1]],
            "negative": scores[ranking[2]]
        })

    return pd.DataFrame(comment_scores)

def analyze_dataset_with_comments(post_path, comments_path, weighted, rows=1000):
    cleaned_post_data = clean_data(post_path, rows)
    cleaned_comments_data = clean_data(comments_path, rows, True)
    data_list = []

    #iterate through the cleaned posts and calculate sentiment scores for each
    for idx, data in cleaned_post_data.iterrows():
        comment_scores = analyze_post_comments(data["Post_ID"], cleaned_comments_data)
        post_scores = analyze_text(data["clean_body"])
        post_scores_df = pd.DataFrame([post_scores], columns=['neutral', 'positive', 'negative'])

        if weighted:
            combined_scores = pd.concat([post_scores_df, comment_scores[['neutral', 'positive', 'negative']]], ignore_index=True)
            average_scores = combined_scores.mean(numeric_only=True)
        else:
            average_comment_scores = comment_scores[['neutral', 'positive', 'negative']].mean(numeric_only=True)
            combined_average_scores = (post_scores_df.iloc[0] + average_comment_scores) / 2

        data_list.append({
            "company": data["Company"], 
            "post_id": data["Post_ID"], 
            "neutral": average_scores.iloc[0] if weighted else combined_average_scores['neutral'],
            "positive": average_scores.iloc[1] if weighted else combined_average_scores['positive'],
            "negative": average_scores.iloc[2] if weighted else combined_average_scores['negative']
        })

    df = pd.DataFrame(data_list)
    if weighted:
        df.to_csv("../data/sentiment_scores_weighted_comments.csv", index=False)
    else:
        df.to_csv("../data/sentiment_scores_unweighted_comments.csv", index=False)
    return df

if __name__ == "__main__":
    # uncomment this to manually load datasets
    # parser = argparse.ArgumentParser("Generate sentiment for a company")
    # parser.add_argument("company", nargs='?', help="Company to generate for all history", type=str)
    # args = parser.parse_args()
    # if args.company is None:
    #     ImportCSVAll.write_to_csv(post_dataset_path, comments_dataset_path)
    # else:
    #     ImportCSV.write_to_csv_single(args.company, post_dataset_path, comments_dataset_path)

    # ////remove the following if manually loading datasets
    parser = argparse.ArgumentParser("Generate sentiment for a company")
    parser.add_argument("overwrite", nargs='?', help="if false then uses files u put in", type=int)

    args = parser.parse_args()
    if args.overwrite:
        print("skipping db read")
    else:
        ImportCSVAll.write_to_csv(post_dataset_path, comments_dataset_path)
    # to here///////
        
    # dataset with just posts
    post_df = analyze_dataset(post_dataset_path)
    # dataset with posts + comments weighted equally
    weighted_df = analyze_dataset_with_comments(post_dataset_path, comments_dataset_path, True)
    # dataset with posts + comments unweighted
    unweighted_df = analyze_dataset_with_comments(post_dataset_path, comments_dataset_path, False)

    # TODO: use a weighted average for posts when we have likes and views

    # group by company and get the average sentiment scores with just posts 
    comp_avg_no_comments_df = post_df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()

    # group by company and get the average sentiment scores with posts and comments weighted equally
    comp_avg_weighted_df = weighted_df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()

    # group by company and get the average sentiment scores with posts and comments unweighted
    company_avg_unweighted_df = unweighted_df.groupby('company')[['neutral', 'positive', 'negative']].mean().reset_index()

    conn = sqlite3.connect('../blind_posts.db')
    now = datetime.datetime.now()

    comp_avg_no_comments_df['date_computed'] = now
    comp_avg_no_comments_df['type'] = 0
    comp_avg_no_comments_df.to_sql('sentiment_scores', conn, if_exists='append', index=False)

    comp_avg_weighted_df['date_computed'] = now
    comp_avg_weighted_df['type'] = 1
    comp_avg_weighted_df.to_sql('sentiment_scores', conn, if_exists='append', index=False)

    company_avg_unweighted_df['date_computed'] = now
    company_avg_unweighted_df['type'] = 2
    company_avg_unweighted_df.to_sql('sentiment_scores', conn, if_exists='append', index=False)

    print('no comments: ', comp_avg_no_comments_df)
    print('weighted comments: ', comp_avg_weighted_df)
    print('unweighted comments: ', company_avg_unweighted_df)