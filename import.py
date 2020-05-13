import csv
import application


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, released_year in reader:
        application.db.execute(
            "INSERT INTO books (isbn, title, author, released_year) VALUES (:isbn, :title, :author,:released_year)",
            {"isbn": isbn, "title": title, "author": author, "released_year": released_year})
        print(f"Added {isbn} ")
    application.db.commit()


if __name__ == "__main__":
    main()
