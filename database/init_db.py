"""
Creates a small sample SQLite database (company.db) so you have real data
to query. Run this once before starting the app:

    python database/init_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "company.db")


def create_and_seed():
    # Remove old db if it exists, so re-running this script is always safe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        """
    )

    customers = [
        (1, "Aoife Kelly", "Ireland"), (2, "Liam O'Brien", "Ireland"),
        (3, "Emma Byrne", "Ireland"), (4, "Noah Fischer", "Germany"),
        (5, "Mia Rossi", "Italy"), (6, "Lucas Martin", "France"),
        (7, "Sofia Garcia", "Spain"), (8, "James Walsh", "Ireland"),
        (9, "Ava Murphy", "Ireland"), (10, "Ethan Novak", "Poland"),
    ]
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?)", customers)

    products = [
        (1, "Wireless Mouse", "Electronics", 19.99),
        (2, "Mechanical Keyboard", "Electronics", 59.99),
        (3, "USB-C Hub", "Electronics", 24.99),
        (4, "Notebook Set", "Stationery", 8.99),
        (5, "Desk Lamp", "Home Office", 34.99),
        (6, "Webcam HD", "Electronics", 45.00),
        (7, "Standing Desk Mat", "Home Office", 29.99),
        (8, "Fountain Pen", "Stationery", 15.50),
    ]
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    # Orders spread across a few months so "last quarter" style
    # questions have something to bite into
    orders = [
        (1, 1, "2026-05-03"), (2, 2, "2026-05-10"), (3, 3, "2026-05-15"),
        (4, 4, "2026-06-02"), (5, 5, "2026-06-08"), (6, 6, "2026-06-20"),
        (7, 7, "2026-07-01"), (8, 8, "2026-07-05"), (9, 9, "2026-07-11"),
        (10, 10, "2026-07-19"), (11, 1, "2026-07-25"), (12, 2, "2026-08-02"),
    ]
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?)", orders)

    order_items = [
        (1, 1, 1, 2), (2, 1, 2, 1), (3, 2, 3, 1), (4, 3, 4, 5),
        (5, 4, 5, 1), (6, 5, 6, 1), (7, 6, 2, 2), (8, 7, 1, 3),
        (9, 8, 7, 1), (10, 9, 8, 2), (11, 10, 3, 1), (12, 11, 2, 1),
        (13, 12, 6, 1), (14, 12, 5, 1),
    ]
    cur.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", order_items)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_and_seed()
