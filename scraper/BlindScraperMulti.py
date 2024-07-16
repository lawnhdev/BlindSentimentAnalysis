import json
import time
import sqlite3
import threading
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from queue import Queue

from selenium.webdriver.common.proxy import Proxy, ProxyType

from datetime import datetime

import locale
locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )

def set_up_blind_post_database():
    # Connect to SQLite database
    conn = sqlite3.connect('../blind_posts.db')
    c = conn.cursor()
    
    # Create Post tables
    c.execute('''CREATE TABLE IF NOT EXISTS Post (
                    Post_ID TEXT, 
                    Headline TEXT,
                    Company TEXT,
                    Text TEXT,
                    Date_Published TEXT,
                    Author TEXT,
                    Comment_Count INTEGER,
                    View_Count INTEGER,
                    Like_Count INTEGER,
                    FOREIGN KEY (Company) REFERENCES Company(Name)
                )''')


    # Create Comment table
    c.execute('''CREATE TABLE IF NOT EXISTS Comment (
                    Comment_ID INTEGER PRIMARY KEY,
                    Post_ID TEXT,
                    Author TEXT,
                    Company TEXT,
                    Level TEXT,
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

def insert_qa_post_to_db(json_data, view_count_str, company, conn, c):
    # Extract post information
    '''

    {
  "@context": "https://schema.org",
  "@type": "QAPage",
  "mainEntity": {
    "@type": "Question",
    "name": "What exactly is Facebook culture?",
    "text": "Heard that Facebook wants to maintain its internal culture at any costs. What exactly is the FB culture?",
    "answerCount": 29,
    "upvoteCount": 3,
    "dateCreated": "2019-12-26T02:00:00.000Z",
    "author": {
      "@type": "Person",
      "name": "Stonks📈"
    },
    "suggestedAnswer": [
      {
        "@type": "Answer",
        "text": "In my experience it&apos;s like a more easy going Google.",
        "dateCreated": "Dec 26, 2019",
        "upvoteCount": 5,
        "url": "https://teamblind.com/post/What-exactly-is-Facebook-culture-MgGKPbmr",
        "author": {
          "@type": "Person",
          "name": "₱"
        }
      },
      {
        "@type": "Answer",
        "text": "It is basically a rat race, that is why &quot;move fast&quot; is one of their values.\n\nAlso, a lot of people like to compare fb with Google. But the truth is,  Facebook is to Google what Kim Kardashian is to Kate Middleton basically.",
        "dateCreated": "Dec 26, 2019",
        "upvoteCount": 11,
        "url": "https://teamblind.com/post/What-exactly-is-Facebook-culture-MgGKPbmr",
        "author": {
          "@type": "Person",
          "name": "ytew"
        }
      },
      {
        "@type": "Answer",
        "text": "Very social atmosphere that encourages advertising at all costs, I would assume.",
        "dateCreated": "Dec 26, 2019",
        "upvoteCount": 4,
        "url": "https://teamblind.com/post/What-exactly-is-Facebook-culture-MgGKPbmr",
        "author": {
          "@type": "Person",
          "name": "reyst"
        }
      }
    ],
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Move fast, break trust",
      "dateCreated": "Dec 26, 2019",
      "upvoteCount": 15,
      "url": "https://teamblind.com/post/What-exactly-is-Facebook-culture-MgGKPbmr",
      "author": {
        "@type": "Person",
        "name": "ABC-CEO"
      }
    }
  }
}

    '''
    question = json_data['mainEntity'].get('name', '')
    text = json_data['mainEntity'].get('text', '')
    date_created = json_data['mainEntity'].get('dateCreated', '')
    upvote_count = json_data['mainEntity'].get('upvoteCount', '') # we will use this later
    answer_count = json_data['mainEntity'].get('answerCount', '')
    author_name = json_data['mainEntity'].get('author', '').get('name', '')

    accepted_answer_text = json_data['mainEntity'].get('acceptedAnswer', '').get('text', '')
    accepted_answer_date_created = json_data['mainEntity'].get('acceptedAnswer', '').get('dateCreated', '')
    accepted_answer_upvote_count = json_data['mainEntity'].get('acceptedAnswer', '').get('upvoteCount', '')
    # for some reason the urls are in the answers and not the question. we will just insert it as the post id
    post_url = json_data['mainEntity'].get('acceptedAnswer', '').get('url', '')
    # Split the URL by '/post/' and take the last part to get the post_id
    post_id = post_url.split('/post/')[-1]
    accepted_answer_author_name = json_data['mainEntity'].get('acceptedAnswer', '').get('author', '').get('name', '')
    # print(f"Q&A Post Views: {view_count_str} and Upvotes: {upvote_count}")
    post_info = (
        post_id,
        question,
        company,
        text,
        date_created,
        author_name,
        answer_count,
        upvote_count,
        locale.atoi(view_count_str),
    )
    print(post_info)

    # Insert post information into Post table
    c.execute('''INSERT INTO Post (Post_ID, Headline, Company, Text, Date_Published, Author, Comment_Count, View_Count, Like_Count)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', post_info)

    accepted_answer_comment_info = (
        post_id,
        accepted_answer_author_name,
        company,
        "parent", # for Q&A comments just setting it as parent for now
        accepted_answer_text,
        accepted_answer_upvote_count,
        accepted_answer_date_created
    )

    # Insert comment information into Comment table
    c.execute('''INSERT INTO Comment (Post_ID, Author, Company, Level, Text, Upvotes, Date_Published)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', accepted_answer_comment_info)

    suggested_answers = json_data['mainEntity'].get('suggestedAnswer', [])
    for suggested_answer in suggested_answers:
        suggested_answer_text = suggested_answer.get('text', '')
        suggested_answer_date_created = suggested_answer.get('dateCreated', '')
        suggested_answer_upvote_count = suggested_answer.get('upvoteCount', '')
        suggested_answer_author_name = suggested_answer.get('author', '').get('name', '')

        suggested_answer_comment_info = (
            post_id,
            suggested_answer_author_name,
            company,
            "parent", # for Q&A comments just setting it as parent for now
            suggested_answer_text,
            suggested_answer_upvote_count,
            suggested_answer_date_created
        )

        # Insert comment information into Comment table
        c.execute('''INSERT INTO Comment (Post_ID, Author, Company, Level, Text, Upvotes, Date_Published)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', suggested_answer_comment_info)

    # Commit changes to the database
    conn.commit()

def insert_discussion_forum_post_to_db(json_data, view_count_str, company, conn, c):
    post_url = json_data.get('url', '')
    # Split the URL by '/post/' and take the last part to get the post_id
    post_id = post_url.split('/post/')[-1]
    # changing to get the post upvote count like this because strangely occasionally
    # the html has no button with the aria-label="Like this post"
    upvote_count = json_data.get('interactionStatistic').get('userInteractionCount') # holds the # of upvotes on the post
    # print(f"Discussion Forum Post Views: {view_count_str} and Upvotes: {upvote_count}")
    post_info = (
        post_id,
        json_data.get('headline', ''),
        company,
        json_data.get('text', ''),
        json_data.get('datePublished', ''),
        json_data.get('author', {}).get('name', ''),
        json_data.get('commentCount', ''),
        locale.atoi(view_count_str),
        upvote_count
    )
    print(post_info)

    # Insert post information into Post table
    c.execute('''INSERT INTO Post (Post_ID, Headline, Company, Text, Date_Published, Author, Comment_Count, View_Count, Like_Count)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', post_info)

    # Extract and insert comments
    comments = json_data.get('comment', [])
    # print(comments)
    for comment in comments:
        # Extract comment information
        author_info = comment.get('author', {})  # Get the author information
        author_name = author_info.get('name', '')  # Get the author's name
        comment_info = (
            post_id,
            author_name,
            company, 
            "parent",
            comment.get('text', ''),  # Get the comment text
            comment.get('upvoteCount', ''), # Get the number of upvotes the comment has
            json_data.get('datePublished', '')  # Use post's date published for comment
        )
        child_comments = comment.get('comment')
        for child_comment in child_comments:
            child_author_info = child_comment.get('author', {})  # Get the author information
            child_author_name = child_author_info.get('name', '')  # Get the author's name
            child_comment_info = (
                post_id,  # Use the current post ID
                child_author_name,
                company,
                "child",
                child_comment.get('text', ''),  # Get the comment text
                child_comment.get('upvoteCount', ''), # Get the number of upvotes the comment has
                json_data.get('datePublished', '')  # Use post's date published for comment
            )
            # Insert comment information into Comment table
            c.execute('''INSERT INTO Comment (Post_ID, Author, Company, Level, Text, Upvotes, Date_Published)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', child_comment_info)
        c.execute('''INSERT INTO Comment (Post_ID, Author, Company, Level, Text, Upvotes, Date_Published)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', comment_info)

    # Commit changes to the database
    conn.commit()

def parse_blind_post_from_url(driver, post_url, company, conn, c, options, windows_flag):
    # Navigate to the post URL
    # print(str(threading.get_native_id()) + str(driver))
    # print(str(threading.get_native_id()) + str(options))
    driver.get(post_url)

    # Extract page source
    page_source = driver.page_source
    # print(page_source)
    # buttons = driver.find_elements_by_class_name('overflow-hidden text-sm font-semibold text-black underline')
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button.overflow-hidden.text-sm.font-semibold.text-black.underline')
        # print(buttons)
    except:
        print("an issue")
    try:
        for button in buttons:
            button.click()
    except:
        print(str(threading.get_native_id()) + ' sign in popup')
        
        # driver.close()
        # driver.get(post_url)
        # page_source = driver.page_source
        driver.quit()
        driver = webdriver.Chrome(options=options)
        # print(str(threading.get_native_id()) + " " + str(driver) + 'new driver')
        driver.get(post_url)
        # print("got post after sign in")
        page_source = driver.page_source

    soup = BeautifulSoup(page_source, 'html.parser')

    if windows_flag:
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
                        if isinstance(json_data, dict):
                            if json_data.get('@type') == 'DiscussionForumPosting':
                                view_count_str = soup.find('button', {'aria-label': 'Views'})['data-count']
                                insert_discussion_forum_post_to_db(json_data, view_count_str, company, conn, c)
                                print('inserted dicussion forum post for ' + company + ' in thread ' + str(threading.get_native_id()))

                            if json_data.get('@type') == 'QAPage':
                                view_count_str = soup.find('button', {'aria-label': 'Views'})['data-count']
                                insert_qa_post_to_db(json_data, view_count_str, company, conn, c)
                                print('inserted Q&A forum post for' + company + 'in thread ' + str(threading.get_native_id()))
                    except json.JSONDecodeError as e:
                        continue  # Every single one will fail except the post we are looking for

    else: # for the other dawgs
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
                    view_count_str = soup.find("button", attrs={ "aria-label": "Views" })["data-count"]
                    insert_discussion_forum_post_to_db(json_data, view_count_str, company, conn, c)
                    print('inserted dicussion forum post for' + company + 'in thread ' + str(threading.get_native_id()))
                    # print('inserted ' + company + 'in thread ' + str(threading.get_native_id()))
                if json_data.get('@type') == 'QAPage':
                    view_count_str = soup.find("button", attrs={ "aria-label": "Views" })["data-count"]
                    insert_qa_post_to_db(json_data, view_count_str, company, conn, c)
                    print('inserted Q&A forum post for' + company + 'in thread ' + str(threading.get_native_id()))
            except json.JSONDecodeError as e:
                continue  # Every single one will fail except the post we are looking for
    return driver


def scrape_company(company, proxy_queue, start_page, end_page, windows_flag):
    proxy = proxy_queue.get()
    print(proxy)
    conn, c = set_up_blind_post_database()
    options = webdriver.ChromeOptions()
    options.add_argument(f'--proxy-server={proxy}')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0')
    driver = webdriver.Chrome(options=options)
    for page in range(start_page, end_page + 1):
        company_trending_posts_url = f'https://www.teamblind.com/company/{company}/posts?page={page}'
        driver.get(company_trending_posts_url)
        page_source = driver.page_source
        # Parse the HTML document using BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        # Find all <a> elements with href attribute starting with "/post/"
        post_links = soup.find_all('a', href=lambda href: href and href.startswith('/post/'))
        # Extract the href attribute from each <a> element
        post_links_urls = [link['href'] for link in post_links]
        if not post_links_urls:
            print(f"No posts found for {company} on page {page}.")
            # free the proxy to be used by other threads by adding it back to the queue
            print(f"Adding proxy {proxy} back to the queue. Exiting thread.")
            proxy_queue.put(proxy)
            driver.quit() # we are ending the thread so close the driver.
            break
        unique_post_link_urls = list(set(post_links_urls))
        for post_url in unique_post_link_urls:
            driver = parse_blind_post_from_url(driver=driver, post_url=blind_home_page_url + post_url, company=company, conn=conn, c=c, options=options, windows_flag=windows_flag)
        conn.close()

def review_company(company):
    # Company review parsing
    company_reviews_url = f'https://www.teamblind.com/company/{company}/reviews'
    conn, c = set_up_blind_post_database()
    # parsing reviews in the main thread
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.get(company_reviews_url)
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
    driver.quit()
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Optional app description')
    # Optional argument
    parser.add_argument('--windows_flag', type=bool,
                        help='An optional boolean argument for how we parse the html script elements based on our local setups')
    args = parser.parse_args()
    windows_flag = False
    if args.windows_flag is not None and args.windows_flag:
        windows_flag = True
    print(windows_flag)
    proxies = ["168.80.164.252:3199", "168.81.85.189:3199", "104.233.49.143:3199", "185.195.214.246:3199", "168.81.68.72:3199",
                   "168.81.214.71:3199", "67.227.127.63:3199", "168.81.71.179:3199", "168.81.85.49:3199", "181.177.71.14:3199",
                   "104.239.114.10:3199", "185.199.118.133:3199", "168.80.149.234:3199", "181.177.64.3:3199", "168.80.183.45:3199",
                   "168.80.151.107:3199", "104.249.2.94:3199", "67.227.125.76:3199", "168.81.231.18:3199", "67.227.123.103:3199",
                   "168.81.102.107:3199", "104.239.112.137:3199", "186.179.27.60:3199", "104.249.1.185:3199", "185.188.78.95:3199",
                   "104.233.52.168:3199", "181.177.65.68:3199", "168.80.149.231:3199", "185.199.116.99:3199", "185.205.197.228:3199",
                   "168.81.68.173:3199", "186.179.1.89:3199", "186.179.21.247:3199", "181.177.66.39:3199",
                   "168.80.180.143:3199", "104.249.2.241:3199", "168.80.135.31:3199", "168.81.214.209:3199",
                   "168.81.213.232:3199", "168.81.215.26:3199"]
    # "GameStop", "Meta"
    companies = ["Google", "Microsoft", "Amazon", "Apple", "Nvidia", "Tesla", "Netflix", "Salesforce", "Reddit",
                 "AMD", "Oracle", "Snowflake", "Uber", "Lyft", "Samsung", "Intel", "PayPal", "Snap",
                 "Palantir", "ByteDance", "Coinbase", "Robinhood", "Block", "Roblox", "Airbnb", "Shopify",
                 "Visa", "CrowdStrike", "Qualcomm", "Adobe", "Cisco", "Accenture", "IBM", "Dell", "Infosys", "Spotify",
                 "Workday", "DoorDash", "Grubhub", "Cognizant", "Starbucks", "ServiceNow", "SoftBank"];
    blind_home_page_url = 'https://www.teamblind.com'
    print('starting')
    threads = []
    num_threads = 20 #40
    total_pages = 400
    proxy_queue = Queue()
    for proxy in proxies:
        proxy_queue.put(proxy)
    company_queue = Queue()
    # Create a dictionary where each company is mapped to num_threads
    company_dict = {company: num_threads for company in companies}
    # Fill company queue with companies to scrape
    for company in companies:
        company_queue.put(company)
        print(f"Parsing company reviews for {company}")
        review_company(company)
        time.sleep(10)
    next_company = company_queue.get()
    curr_company = next_company
    for i in range(num_threads):
        print('starting thread ' + str(i) + ' ' + curr_company)
        start_page = (i * total_pages // num_threads) + 1
        end_page = ((i + 1) * total_pages // num_threads)
        if i == num_threads - 1:
            end_page = total_pages  # Last thread handles the remaining pages
        print(start_page)
        print(end_page)
        t = threading.Thread(target=scrape_company, args=(curr_company, proxy_queue, start_page, end_page, windows_flag))
        t.start()
        threads.append(t)
    for th in threads:
        th.join
    print('donesies')

    # Monitor and manage threads dynamically
    num_free_threads = 0
    while threads:
        for th in threads:
            if not th.is_alive():
                threads.remove(th)  # Remove completed thread
                print("Removing thread!")
                num_free_threads += 1
                company_dict[curr_company] -= 1
        # if we have available threads and the current company hasn't finished yet
        if num_free_threads > 0 and company_dict[curr_company] > 0:
            if curr_company == next_company:
                next_company = company_queue.get()
            print(f"Curr company: {curr_company}")
            print(f"Next company: {next_company}")
            print(f"# of Free Threads: {num_free_threads}")
            print(f"# of Working Threads for {curr_company}: {company_dict[curr_company]}")
            print(f"# of Working Threads for {next_company}: {(num_threads - company_dict[next_company])}")
            next_company_remaining_threads = company_dict[next_company]
            start_page = ((num_threads - next_company_remaining_threads) * total_pages // num_threads) + 1
            end_page = (((num_threads - next_company_remaining_threads) + 1) * total_pages // num_threads)
            print(start_page)
            print(end_page)
            t = threading.Thread(target=scrape_company, args=(next_company, proxy_queue, start_page, end_page, windows_flag))
            t.start()
            num_free_threads -= 1
            next_company_remaining_threads -= 1
            company_dict[next_company] = next_company_remaining_threads
        elif company_dict[curr_company] <= 0:
            curr_company = next_company
