import json
import time
import sqlite3
import threading

from selenium import webdriver
from bs4 import BeautifulSoup

from selenium.webdriver.common.proxy import Proxy, ProxyType

from datetime import datetime

import locale
locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

def inc_proxy():
    global proxy_num
    if(proxy_num == 4):
        proxy_num = 0
    else:
        proxy_num+=1

def set_up_blind_post_database():
    # Connect to SQLite database
    conn = sqlite3.connect('blind_posts.db')
    c = conn.cursor()
    
    # Create Post table
    c.execute('''CREATE TABLE IF NOT EXISTS Post (
                    Post_ID INTEGER PRIMARY KEY,
                    Headline TEXT,
                    Company TEXT,
                    Text TEXT,
                    Date_Published TEXT,
                    URL TEXT,
                    Author TEXT,
                    Comment_Count INTEGER,
                    FOREIGN KEY (Company) REFERENCES Company(Name)
                )''')

    # Create Comment table
    c.execute('''CREATE TABLE IF NOT EXISTS Comment (
                    Comment_ID INTEGER PRIMARY KEY,
                    Post_ID INTEGER,
                    Author TEXT,
                    Text TEXT,
                    Upvotes INTEGER,
                    Date_Published TEXT,
                    FOREIGN KEY (Post_ID) REFERENCES Post(Post_ID)
                )''')

    # Create Company table
    c.execute('''CREATE TABLE IF NOT EXISTS Company(
                    Name TEXT PRIMARY KEY,
                    Ticker TEXT,
                    Btb_Score FLOAT, 
                    Last_Updated TEXT
              )''')    

    # Create CompanyReviews table
    c.execute('''CREATE TABLE IF NOT EXISTS CompanyReviews(
                    Review_ID INTEGER PRIMARY KEY,
                    Company TEXT,
                    Review_Count INTEGER,
                    Created_Date TEXT,
                    Score FLOAT,
                    Career_Growth FLOAT,
                    Work_Life_Balance FLOAT,
                    Comp_Benefits FLOAT,
                    Culture FLAT,
                    Management FLOAT,
                    FOREIGN KEY (Company) REFERENCES Company(Name)
              )''')

    # Return connection and cursor
    return conn, c

def insert_blind_post_to_db(json_data, company, conn, c):
    # Extract post information
    post_info = (
        json_data.get('headline', ''),
        company,
        json_data.get('text', ''),
        json_data.get('datePublished', ''),
        json_data.get('url', ''),
        json_data.get('author', {}).get('name', ''),
        json_data.get('commentCount', '')
    )

    # Insert post information into Post table
    c.execute('''INSERT INTO Post (Headline, Company, Text, Date_Published, URL, Author, Comment_Count)
                  VALUES (?, ?, ?, ?, ?, ?, ?)''', post_info)

    # Get the current post ID
    post_id = c.lastrowid

    # Extract and insert comments
    comments = json_data.get('comment', [])
    for comment in comments:
        # Extract comment information
        author_info = comment.get('author', {})  # Get the author information
        author_name = author_info.get('name', '')  # Get the author's name
        comment_info = (
            post_id,  # Use the current post ID
            author_name,
            comment.get('text', ''),  # Get the comment text
            comment.get('upvoteCount', ''), # Get the number of upvotes the comment has
            json_data.get('datePublished', '')  # Use post's date published for comment
        )

        # Insert comment information into Comment table
        c.execute('''INSERT INTO Comment (Post_ID, Author, Text, Upvotes, Date_Published)
                      VALUES (?, ?, ?, ?, ?)''', comment_info)

    # Commit changes to the database
    conn.commit()

def parse_blind_post_from_url(driver, post_url, company, conn, c):
    # Navigate to the post URL
    driver.get(post_url)

    # Extract page source
    page_source = driver.page_source

    # Parse the HTML document using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all <script> elements
    script_elements = soup.find_all('script', {'type': 'application/ld+json'})
    
    # Iterate over each script element to find the one containing the desired data
    for script in script_elements:
        # print(script)
        try:
            # Parse the JSON data
            json_data = json.loads(script.string) # https://stackoverflow.com/questions/25613565/python-json-loads-returning-string-instead-of-dictionary
            #print(json_data)
            if json_data.get('@type') == 'DiscussionForumPosting':
                insert_blind_post_to_db(json_data, company, conn, c)
                print('inserted ' + company + 'in thread ' + str(threading.get_native_id()))
        except json.JSONDecodeError as e:
            continue  # Every single one will fail except the post we are looking for

# Close connection
def scrape_company(company, proxy):
    conn, c = set_up_blind_post_database()
    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(options=options)

    # Company review parsing
    company_reviews_url = f'https://www.teamblind.com/company/{company}/reviews'
    driver.get(company_reviews_url)
    time.sleep(10)
    try:
        current_timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        # TODO why is soup.string sometimes "None"?
        review_section = soup.find("h1", class_="text-xl").parent
        score_section = review_section.find("h2").parent
        score = score_section.find("h2").text
        review_count = score_section.find("p").text.split(" Reviews")[0]
        review_categories = review_section.find("div", class_="grid").findAll("div", class_="flex")
        # Order of categories: career growth, work life, comp/benefits, culture, management
        get_category_score = lambda category: category.find("div", class_="font-semibold").text
        career_growth = get_category_score(review_categories[0])
        work_life = get_category_score(review_categories[1])
        comp_benefits = get_category_score(review_categories[2])
        culture = get_category_score(review_categories[3])
        management = get_category_score(review_categories[4])
        # Insert company to company table if it doesn't exist
        res = c.execute('''SELECT Name FROM Company WHERE Name=?''', (company,))
        if res.fetchone() == None:
            company_info = (
                company,
                "",
                0.0,
                current_timestamp
            )
            c.execute(''' 
                INSERT INTO Company (Name, Ticker, Btb_Score, Last_Updated)
                 VALUES (?, ?, ?, ?)''', company_info)
            conn.commit()
        # Insert company reviews. Only add a new review if the count changed.
        res = c.execute('''SELECT Review_Count FROM CompanyReviews WHERE Company=?''', (company,))
        res = res.fetchone()
        review_count = locale.atoi(review_count)
        if res == None or (res != None and res[0] > review_count):
            company_reviews_info = (
                company,
                review_count,
                current_timestamp,
                float(score),
                float(career_growth),
                float(work_life),
                float(comp_benefits),
                float(culture),
                float(management)
            )
            c.execute('''
                INSERT INTO CompanyReviews (Company, Review_Count, Created_Date, Score, Career_Growth, Work_Life_Balance, Comp_Benefits, Culture, Management)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (company_reviews_info))
            conn.commit()
    except Exception as error:
        print(f"Caught error while fetching review data for company {company}: {error}")
    
    # Company posts parsing
    company_trending_posts_url = f'https://www.teamblind.com/company/{company}/posts?page={i}'
    driver.get(company_trending_posts_url)
    time.sleep(10)
    page_source = driver.page_source
    # Parse the HTML document using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    # Find all <a> elements with href attribute starting with "/post/"
    post_links = soup.find_all('a', href=lambda href: href and href.startswith('/post/'))
    # Extract the href attribute from each <a> element
    post_links_urls = [link['href'] for link in post_links]
    unique_post_link_urls = list(set(post_links_urls))
    for post_url in unique_post_link_urls:
        parse_blind_post_from_url(driver=driver, post_url=blind_home_page_url + post_url, company=company, conn=conn, c=c)
        time.sleep(10)
    
    conn.close()

        
if __name__ =="__main__":
    proxies = ["168.81.214.71:3199", "67.227.127.63:3199", "168.81.71.179:3199","168.81.85.49:3199","181.177.71.14:3199"]

    blind_home_page_url = 'https://www.teamblind.com'
    companies = ["Meta","Google","Cisco","Oracle","Airbnb"]
    print('starting')
    threads = []
    for i in range(0,5):
        print('starting thread' + str(i) + companies[i])
        t = threading.Thread(target=scrape_company, args=(companies[i],proxies[i]))
        t.start()
        threads.append(t)
    for th in threads:
        th.join
    print('donesies')