from Cleaner import clean_post_data
import pprint
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.downloader.download('vader_lexicon')

dataset_path = "../data/english_financial_news_v2.csv"

if __name__ == "__main__":
  cleaned_data = clean_post_data(dataset_path)
  sentiment_scores = {}
  
  for idx, data in cleaned_data.iterrows():
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(data["clean_body"])

    if scores["pos"] > 0.5 or scores["neg"] > 0.5:
      sentiment_scores[data["newssource"]] = { "body": data["clean_body"], "scores": scores }
    else:
      continue
    

  pprint.pp(sentiment_scores)
  