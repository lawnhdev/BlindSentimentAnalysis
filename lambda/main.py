import logging
import json
import boto3
import uuid
import time
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup


logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    logger.info(f"Post information: {post_info}")

    # Insert post information into DynamoDB table
    ddb.put_item(
        TableName='Posts',
        Item=post_info
    )

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
    time.sleep(15)

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
                    logger.info(f"JSON DATA: {json_data}")
                    if isinstance(json_data, dict) and json_data.get('@type') == 'DiscussionForumPosting': # include check for type 'QAPage' instead of only DiscussionForumPosting
                        insert_blind_post_to_db(json_data, company)
                except json.JSONDecodeError as e:
                    continue  # Every single one will fail except the post we are looking for


def initialise_driver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    #chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    #chrome_options.add_argument(f"--data-path={mkdtemp()}")
    #chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    #chrome_options.add_argument("--remote-debugging-pipe")
    #chrome_options.add_argument("--verbose")
    #chrome_options.add_argument("--log-path=/tmp")
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0')
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    return driver


def lambda_handler(event, context):
    # Log the entire event as a string
    logger.info("Received event: %s", json.dumps(event))
    # Initialize a WebDriver instance
    driver = initialise_driver()
    # Process each message from the SQS event
    responses = []
    for record in event['Records']:
        # Parse the message body (assuming it's in JSON format)
        message = json.loads(record['body'])

        # Extract URL from the message body
        url = message['url']
        company = message['company']

        logger.info(f"Post URL: {url}")
        parse_blind_post_from_url(driver=driver, post_url=url, company=company)

        '''
        {
          "url": "https://www.teamblind.com/post/ne4wCPL0",
          "company": "Meta"
        }
        '''

        # Prepare response body
        body = {
            "url": url,
            "company": company
        }

        # Append the response to the list
        responses.append({
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(body)
        })

    driver.quit()
    # Return all responses as a list
    return responses