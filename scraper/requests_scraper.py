import requests
from requests_ip_rotator import ApiGateway, EXTRA_REGIONS
import json
from bs4 import BeautifulSoup
import uuid

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
    print(f"Post information: {post_info}")


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


# Define a custom User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

gateway = ApiGateway("https://www.teamblind.com/post/MQEMwEKg")
gateway.start()

session = requests.Session()
session.mount("https://www.teamblind.com/post/MQEMwEKg", gateway)
session.headers.update(headers)

response = session.get("https://www.teamblind.com/post/MQEMwEKg") # this doesn't work because the information we need is in the script elements after the javascript is loaded, which requests library doesn';t help us with.
# Pretty print the JSON response content
soup = BeautifulSoup(response.content, 'html.parser')
pretty_html = soup.prettify()
print(pretty_html)
# Find all <script> elements
script_elements = soup.find_all('script')


# Iterate over each script element to find the one containing the desired data
for script in script_elements:
    # print(script)
    if 'self.__next_f.push' in script.text:
        # Split the script text by the prefix to isolate the JSON data
        split_data = script.text.split('self.__next_f.push([1,')

        # Check if the split operation was successful
        if len(split_data) > 1:
            try:
                stripped_data = split_data[1].rstrip('])')
                # Parse the JSON data
                json_data = json.loads(json.loads(stripped_data)) # https://stackoverflow.com/questions/25613565/python-json-loads-returning-string-instead-of-dictionary
                if isinstance(json_data, dict) and json_data.get('@type') == 'DiscussionForumPosting': # include check for type 'QAPage' instead of only DiscussionForumPosting
                    insert_blind_post_to_db(json_data, 'Meta')
            except json.JSONDecodeError as e:
                continue  # Every single one will fail except the post we are looking for

# Only run this line if you are no longer going to run the script, as it takes longer to boot up again next time.
gateway.shutdown()