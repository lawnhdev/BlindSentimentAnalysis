import json
import time
import sqlite3

from selenium import webdriver
from bs4 import BeautifulSoup

'''
   Example data:
   
post_data = {
    "Headline": "Meta onsite interview",
    "Text": "I gave 3 rounds of Meta (2 coding went great, system design went average/above average acc to me), behavioral is in couple of days.\n\nSolved 2-2 questions in both coding rounds with optimized approach. Questions were (Easy/Medium) and (Medium/Hard) in respective coding rounds.\n\nI am not even sure how design round went. Interviewer didn't talk much except for the 2-3 points he had concern on and i fixed it immediately. I explained low level design, went on scaling part and then interview time over.\n\nIt will be for E4/E5 SWE. What are the odds of getting offer and at which level?\n\nAlso, how much behavioral interview weigh in Meta?\n\nYoe - 8",
    "Date_Published": "2024-06-06T04:00:00.000Z",
    "URL": "https://www.teamblind.com/post/HLBxUXQV",
    "Author": "GYIH14",
    "Comment_Count": 10
}

comment_data = {
    "Post_ID": 1,
    "Author": "dtynvbn",
    "Text": "System-design and behavioural performance matters a lot in deciding level(E5)",
    "Upvotes": 1,
    "Date_Published": "2024-06-06T04:00:00.000Z"
}

'''
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
                    Comment_Count INTEGER
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

def parse_blind_post_from_url(driver, post_url, company):
    # Navigate to the post URL
    driver.get(post_url)


    # Extract page source
    page_source = driver.page_source

    # Parse the HTML document using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all <script> elements
    script_elements = soup.find_all('script')

    # Iterate over each script element to find the one containing the desired data
    for script in script_elements:
        if 'self.__next_f.push' in script.text:
            # Split the script text by the prefix to isolate the JSON data
            split_data = script.text.split('self.__next_f.push([1,')

            # Check if the split operation was successful
            if len(split_data) > 1:
                try:
                    stripped_data = split_data[1].rstrip('])')
                    # Parse the JSON data
                    json_data = json.loads(json.loads(stripped_data)) # https://stackoverflow.com/questions/25613565/python-json-loads-returning-string-instead-of-dictionary
                    if isinstance(json_data, dict) and json_data.get('@type') == 'DiscussionForumPosting':
                        insert_blind_post_to_db(json_data, company, conn, c)
                except json.JSONDecodeError as e:
                    continue  # Every single one will fail except the post we are looking for


options = webdriver.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
driver = webdriver.Chrome(options=options)

blind_home_page_url = 'https://www.teamblind.com'
conn, c = set_up_blind_post_database()
companies = ["Meta"]
for company in companies:
    # we are going to collect all the trending posts on the first five pages for a given company
    for i in range(1, 6):
        company_trending_posts_url = f'https://www.teamblind.com/company/{company}/posts?page={i}'
        driver.get(company_trending_posts_url)
        time.sleep(10)

        # Extract page source
        page_source = driver.page_source
        # Parse the HTML document using BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        # Find all <a> elements with href attribute starting with "/post/"
        post_links = soup.find_all('a', href=lambda href: href and href.startswith('/post/'))
        # Extract the href attribute from each <a> element
        post_links_urls = [link['href'] for link in post_links]

        unique_post_link_urls = list(set(post_links_urls))
        for post_url in unique_post_link_urls:
            parse_blind_post_from_url(driver=driver, post_url=blind_home_page_url + post_url, company=company)
            time.sleep(10)

# Close connection
conn.close()