import boto3
import json
import time
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Initialize Boto3 DynamoDB client
ddb = boto3.client('dynamodb', region_name='us-east-1')

def insert_blind_post_to_db(json_data, company):
    # Extract post information
    post_id = str(uuid.uuid4())
    post_info = {
        'postId': {'S': post_id},  # Generate a unique postId (using UUID for example)
        'Headline': {'S': json_data.get('headline', '')},
        'Company': {'S': company},
        'Text': {'S': json_data.get('text', '')},
        'Date_Published': {'S': json_data.get('datePublished', '')},
        'URL': {'S': json_data.get('url', '')},
        'Author': {'S': json_data.get('author', {}).get('name', '')},
        'Comment_Count': {'N': str(json_data.get('commentCount', ''))}
    }

    print(post_info)

    # Insert post information into DynamoDB table
    ddb.put_item(
        TableName='Posts',
        Item=post_info
    )

    '''
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

    '''

    # Extract and insert comments
    comments = json_data.get('comment', [])
    for count, comment in enumerate(comments, start=1):
        # Extract comment information
        author_info = comment.get('author', {})  # Get the author information
        author_name = author_info.get('name', '')  # Get the author's name
        comment_info = {
            'commentId': {'S': str(uuid.uuid4())},  # Generate a unique commentId
            'postId': {'S': post_id},  # Use the postId of the current post
            'Author': {'S': author_name},
            'Text': {'S': comment.get('text', '')},
            'Upvotes': {'N': str(comment.get('upvoteCount', ''))},
            'Date_Published': {'S': json_data.get('datePublished', '')}
        }

        # Insert comment information into DynamoDB table
        ddb.put_item(
            TableName='Comments',
            Item=comment_info
        )

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
                        insert_blind_post_to_db(json_data, company)
                except json.JSONDecodeError as e:
                    continue  # Every single one will fail except the post we are looking for


# Specify the path to the chromedriver executable
chromedriver_path = '/usr/local/bin/chromedriver'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--enable-javascript')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0')
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
# Specify the path to the Chrome binary (not Chromedriver)
options.binary_location = '/usr/local/bin/google-chrome'
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)


blind_home_page_url = 'https://www.teamblind.com'
blind_posts_table_name = 'Posts'
blind_comments_table_name = 'Comments'

# Load the list of companies from the JSON file
with open('/home/ec2-user/companies.json', 'r') as f:
   companies = json.load(f)
print(companies)

for company in companies:
    # we are going to collect all the trending posts on the first 10 pages for a given company
    for i in range(1, 11):
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

driver.quit()