BEGIN TRANSACTION;
CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL
        );
INSERT INTO "books" VALUES(1,'Clean Code','Robert C. Martin');
INSERT INTO "books" VALUES(2,'The Pragmatic Programmer','Andrew Hunt');
CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (book_id) REFERENCES books (id)
        );
INSERT INTO "orders" VALUES(1,1,2,'completed');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('books',2);
INSERT INTO "sqlite_sequence" VALUES('orders',1);
COMMIT;
