import boto3
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Specify the path to the chromedriver executable
chromedriver_path = '/usr/local/bin/chromedriver'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
# options.add_argument('--enable-javascript')
options.add_argument('--disable-gpu')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0')
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
# Specify the path to the Chrome binary (not Chromedriver)
options.binary_location = '/usr/local/bin/google-chrome'
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)


blind_home_page_url = 'https://www.teamblind.com'
# Initialize SQS client
sqs = boto3.client('sqs', region_name='us-east-1')  # Replace with your region

# Load the list of companies from the JSON file
with open('/home/ec2-user/companies.json', 'r') as f:
   companies = json.load(f)
print(companies)

# Read queue URL from file
with open('/home/ec2-user/queue_url.txt', 'r') as f:
    queue_url = f.read().strip()
print(queue_url)

count = 0
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
            full_post_url = blind_home_page_url + post_url
            message_body = {
                'url': full_post_url,
                'company': company
            }

            # Send message to SQS
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body)
            )

            print(f"Sent message to SQS: {response['MessageId']}")
            count += 1

driver.quit()
print(count)

# lawnh_2: AKIA2UC3DIUSEBMAPX7V umABEbwg5RoiCBKNCcsB7hf9GYY23Vt21MDeRSbB