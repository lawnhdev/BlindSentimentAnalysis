import json
import time

from selenium import webdriver
from bs4 import BeautifulSoup

def dump_blind_post_info(json_data):
    print("Post Information:")
    print("Headline:", json_data.get('headline', ''))
    print("Text:", json_data.get('text', ''))
    print("Date Published:", json_data.get('datePublished', ''))
    print("URL:", json_data.get('url', ''))
    print("Author:", json_data.get('author', {}).get('name', ''))
    print("Comment Count:", json_data.get('commentCount', ''))
    print()
    comments = json_data.get('comment', [])
    for comment in comments:
        author_info = comment.get('author', {})  # Get the author information
        author_name = author_info.get('name', '')  # Get the author's name
        print("Author: ", author_name)
        comment_text = comment.get('text', '')  # Get the comment text
        print("Comment: ", comment_text)
        upvote_count = comment.get('upvoteCount', '') # Get the number of upvotes the comment has
        print("# of Upvotes: ", upvote_count)
        print("Date Published: ", json_data.get('datePublished', ''))
        print()  # Print a blank line for readability

def parse_blind_post_from_url(driver, post_url):
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
                        dump_blind_post_info(json_data)
                except json.JSONDecodeError as e:
                    continue  # Every single one will fail except the post we are looking for


options = webdriver.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
driver = webdriver.Chrome(options=options)

blind_home_page_url = 'https://www.teamblind.com'
# we are going to collect all the trending posts on the first five pages for a given company
for i in range(1, 6):
    company_trending_posts_url = f'https://www.teamblind.com/company/Meta/posts?page={i}'
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
        parse_blind_post_from_url(driver=driver, post_url=blind_home_page_url + post_url)
        time.sleep(10)