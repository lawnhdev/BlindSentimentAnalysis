from transformers import AutoModelForSequenceClassification
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoConfig
import numpy as np
import pandas as pd
import pprint
from scipy.special import softmax
from Cleaner import clean_post_data
from transformers import logging
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
        #change this to post_id in final implementation
        data_list.append({
            "body": data["clean_body"],
            "neutral": scores[ranking[0]],
            "positive": scores[ranking[1]],
            "negative": scores[ranking[2]]
        })

    pprint.pp(data_list)

    # instead of writing to a csv itll be written to the db
    pd.DataFrame(data_list).to_csv("../data/sentiment_scores.csv", index=False)

if __name__ == "__main__":
    analyze_dataset(dataset_path)

        



    