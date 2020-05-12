import csv
import application


f = open("books.csv")

reader = csv.reader(f)

for isbn,title,author,year in reader:
    application.db.execute("INSERT INTO books (isbn,title,author,released_year) VALUES (:isbn,:title,:author,:released_year)",
                           {"isbn":isbn,"title":title,"author":author,"released_year":year})
    print(f"Added books {isbn}")
    application.db.commit()