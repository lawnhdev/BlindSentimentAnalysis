import sqlite3
import random
from datetime import datetime, timedelta
import numpy as np
companies = ["Meta","Google","Cisco","Oracle","Airbnb"]
conn = sqlite3.connect('../blind_posts.db')
c = conn.cursor()
c.execute('''CREATE TABLE "sentiment_scores" (
    "company" TEXT,
    "neutral" REAL,
    "positive" REAL,
    "negative" REAL,
    "date_computed" TIMESTAMP,
    "type" INTEGER
    )''')
for i in range(0,5):
    rand = random.random()
    for k in range(0,100):
        random_numbers = np.random.dirichlet([1, 1, 1])
        rand2 = random.random()
        sentiment = (
            # k,
            companies[i],
            random_numbers[0],
            random_numbers[1],
            random_numbers[2],
            datetime.now() + timedelta(days=-k), 
            # left as 0 for now, maybe %3 to get spread for later idk how to use rn
            0
        )
        c.execute('''INSERT INTO sentiment_scores (company, neutral, positive, negative, date_computed, type) VALUES (?, ?, ?, ?, ?, ?)''', sentiment)
        conn.commit()
conn.close()