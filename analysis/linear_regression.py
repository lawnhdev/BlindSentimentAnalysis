import matplotlib.pyplot as plt
import yfinance as yf

if __name__ == "__main__":
  meta = yf.Ticker("META")
  history = meta.history(period="1mo")
  history["Close"].plot()
  plt.title("Meta Stock Prices")
  plt.show()