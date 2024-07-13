from Cleaner import clean_post_data
import pprint
from transformers import pipeline 

sentiment = pipeline('sentiment-analysis', return_all_scores=True)
dataset_path = "../data/stock_market_tweets.csv"

if __name__ == "__main__":
  cleaned_data = clean_post_data(dataset_path)
  sentiment_scores = {}

  for idx, data in cleaned_data.iterrows():
    score_arr = sentiment("clean_body")
    
    if idx == 100:
      break

    sentiment_scores[data["tweet_id"]] = { "body": data["clean_body"], "score": score_arr}
  
  ### For some reason all tweets are marked as positive with the same value.
  pprint.pp(sentiment_scores)
  print(sentiment_scores.__len__())