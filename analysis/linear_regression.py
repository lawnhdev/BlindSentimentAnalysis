import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import pandas as pd

from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
from datetime import datetime

def plot_sentiment(dates, values, label, color):
  dates = dates.to_numpy()
  values = values.to_numpy()

  # X axis train and testing data
  sentiment_x_train = dates[:-20]
  sentiment_x_test = dates[-20:]
  
  # Y axis train and testing data
  sentiment_y_train = values[:-20]
  sentiment_y_test = values[-20:]

  # Create linear regression object
  regr = linear_model.LinearRegression()

  # Train the model using the training sets
  regr.fit(sentiment_x_train, sentiment_y_train)

  # Make predictions using the testing set
  sentiment_y_pred = regr.predict(sentiment_x_test)

  # The coefficients
  print("Coefficients: \n", regr.coef_)
  # The mean squared error
  print("Mean squared error: %.2f" % mean_squared_error(sentiment_y_test, sentiment_y_pred))
  # The coefficient of determination: 1 is perfect prediction
  print("Coefficient of determination: %.2f" % r2_score(sentiment_y_test, sentiment_y_pred))

  # Plot outputs
  plt.scatter(sentiment_x_test, sentiment_y_test, color="black")
  plt.plot(sentiment_x_test, sentiment_y_pred, color=color, linewidth=3, label=label)

  plt.xticks(())
  plt.yticks(())
  plt.title("Linear Regression Test")


if __name__ == "__main__":
  conn = sqlite3.connect("../blind_posts.db")
  c = conn.cursor()

  # Get all meta sentiment values for now
  # [neutral, positive, negative, date_computed]
  res = c.execute('''
                    SELECT neutral, positive, negative, date_computed FROM sentiment_scores WHERE company='Meta'
                  ''')  
  arr = res.fetchall()

  df = pd.DataFrame(arr, columns=["neu", "pos", "neg", "date"])
  df["date"] = pd.to_datetime(df["date"]).astype(int)

  # Plot neutral, positive, and negative values
  colors=["red", "blue", "green"]
  arr = ["neu", "pos", "neg"]
  for i in range(len(arr)): 
    plot_sentiment(df[["date"]], df[[arr[i]]], arr[i], colors[i])
  plt.show()