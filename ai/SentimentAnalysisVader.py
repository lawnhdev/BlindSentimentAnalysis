
from Cleaner import clean_data
import pprint
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.downloader.download('vader_lexicon')

dataset_path = "../data/stock_market_tweets.csv"

if __name__ == "__main__":
  cleaned_data = clean_data(dataset_path)
  sentiment_scores = {}
  
  for idx, data in cleaned_data.iterrows():
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(data["clean_body"])

    if idx == 10000:
      break   

    if scores["neu"] > 0.5:
      continue

    sentiment_scores[data["tweet_id"]] = { "body": data["clean_body"]}
    

  pprint.pp(sentiment_scores)
  