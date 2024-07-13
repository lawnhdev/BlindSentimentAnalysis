import csv
import sqlite3

def write_to_csv():
    dataset_path = "../data/Post.csv"

    conn = sqlite3.connect('../blind_posts.db')
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Post')
    # extend this with comments if want
    with open(dataset_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # field = ["Post_ID" ,"Headline,Company" ,"Text","Date_Published","URL","Author","Comment_Count"]
        writer.writerow([d[0] for d in cursor.description])
        for result in cursor:
            writer.writerow(result)

    cursor.close()


if __name__ == '__main__':
    write_to_csv()