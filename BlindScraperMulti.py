import json
import time
import sqlite3
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from selenium.webdriver.common.proxy import Proxy, ProxyType



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

    # print(json_data)
    # Extract and insert comments
    comments = json_data.get('comment', [])
    # print(comments)
    for comment in comments:
        print(comment)
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

def parse_blind_post_from_url(driver, post_url, company, conn, c, options):
    # Navigate to the post URL
    print(str(threading.get_native_id()) + str(driver))
    print(str(threading.get_native_id()) + str(options))
    driver.get(post_url)


    # Extract page source
    page_source = driver.page_source
    # print(page_source)
    # buttons = driver.find_elements_by_class_name('overflow-hidden text-sm font-semibold text-black underline')
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button.overflow-hidden.text-sm.font-semibold.text-black.underline')
        print(buttons)
    except:
        print("an issue")
    try:
        for button in buttons:
            button.click()
    except:
        print(str(threading.get_native_id()) + 'sign in popup')
        
        # driver.close()
        # driver.get(post_url)
        # page_source = driver.page_source
        driver.quit()
        driver = None
        time.sleep(10)
        driver = webdriver.Chrome(options=options)
        print(str(threading.get_native_id()) + str(driver) + 'new driver')
        driver.get(post_url)
        # print("got post after sign in")
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
            # print(json_data)
            if json_data.get('@type') == 'DiscussionForumPosting':
                insert_blind_post_to_db(json_data, company, conn, c)
                # print('inserted ' + company + 'in thread ' + str(threading.get_native_id()))
        except json.JSONDecodeError as e:
            continue  # Every single one will fail except the post we are looking for
    return driver


# Close connection

def scrape_company(company, proxy):
    conn, c = set_up_blind_post_database()
    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(options=options)

    company_trending_posts_url = f'https://www.teamblind.com/company/{company}/posts?page={i}'
    driver.get(company_trending_posts_url)
    # time.sleep(10)
    page_source = driver.page_source
    # Parse the HTML document using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    # Find all <a> elements with href attribute starting with "/post/"
    post_links = soup.find_all('a', href=lambda href: href and href.startswith('/post/'))
    # Extract the href attribute from each <a> element
    post_links_urls = [link['href'] for link in post_links]
    unique_post_link_urls = list(set(post_links_urls))
    p = 0
    for post_url in unique_post_link_urls:
        print(str(threading.get_native_id()) + str(driver) + 'scrape_company')
        driver = parse_blind_post_from_url(driver = driver, post_url=blind_home_page_url + post_url, company=company, conn=conn, c=c, options=options)
        # time.sleep(10)
        print(str(threading.get_native_id()) +'current count is ' + str(p))
        p+=1
    conn.close()

        
if __name__ =="__main__":
    # proxies = ["168.81.214.71:3199", "67.227.127.63:3199", "168.81.71.179:3199","168.81.85.49:3199","181.177.71.14:3199"]
    proxies = ["168.80.164.252:3199", "168.81.85.189:3199", "104.233.49.143:3199"]

    blind_home_page_url = 'https://www.teamblind.com'
    companies = ["Meta","Google","Cisco","Oracle","Airbnb"]
    print('starting')
    threads = []
    for i in range(0,3):
        print('starting thread' + str(i) + companies[i])
        t = threading.Thread(target=scrape_company, args=(companies[i],proxies[i]))
        t.start()
        threads.append(t)
    for th in threads:
        th.join
    print('donesies')