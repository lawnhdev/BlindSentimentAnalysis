import csv
import sqlite3

def write_to_csv(dataset_path, comments_dataset_path):

    conn = sqlite3.connect('../blind_posts.db')
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Post')
    # extend this with comments if want
    with open(dataset_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([d[0] for d in cursor.description])
        for result in cursor:
            writer.writerow(result)
    cursor.execute(f'SELECT * FROM Comment')
    with open(comments_dataset_path, 'w', newline='') as c_file:
        c_writer = csv.writer(c_file)
        print(cursor.description)
        c_writer.writerow([d[0] for d in cursor.description])
        for result in cursor:
            c_writer.writerow(result)
    cursor.close()


if __name__ == '__main__':
    write_to_csv()