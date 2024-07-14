import csv
import sqlite3

def write_to_csv(dataset_path, comments_dataset_path, checkpoint = False):
    
    conn = sqlite3.connect('../blind_posts.db')
    cursor = conn.cursor()
    if checkpoint:
        #get the last time the sentiment analysis bot was run
        cursor.execute(f'SELECT MAX(date_computed) FROM sentiment_scores')
        newest_date = cursor.fetchone()[0]
        #only get the posts that have been added since the last time the sentiment analysis bot was run
        cursor.execute(f'SELECT * FROM Post WHERE Date_Published >= "{newest_date}"')
        posts = cursor.fetchall()
        post_ids = [post[0] for post in posts]  
    else:
        cursor.execute(f'SELECT * FROM Post')
    # extend this with comments if want
    with open(dataset_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([d[0] for d in cursor.description])
        for result in cursor:
            writer.writerow(result)

    # Get comments that have a Post_ID in the result of the previous query
    if checkpoint and post_ids:
        placeholders = ', '.join('?' for unused in post_ids)
        cursor.execute(f'SELECT * FROM Comment WHERE Post_ID IN ({placeholders})', post_ids)
    else:
        cursor.execute('SELECT * FROM Comment')
    with open(comments_dataset_path, 'w', newline='') as c_file:
        c_writer = csv.writer(c_file)
        c_writer.writerow([d[0] for d in cursor.description])
        for result in cursor:
            c_writer.writerow(result)
    cursor.close()


if __name__ == '__main__':
    write_to_csv()