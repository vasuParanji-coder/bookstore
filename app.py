from flask import Flask, render_template, request, redirect
import psycopg2
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="bookstore_db",
        user="store_user",
        password="vasu1234"
    )
    return conn

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/available_books')
def available_books():
    conn = get_db_connection()
    cur = conn.cursor()
    query = 'SELECT * FROM available_books'
    cur.execute(query)
    books = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('available_books.html', books=books)

@app.route('/purchase_books')
def purchase_books():
    conn = get_db_connection()
    cur = conn.cursor()
    query = 'SELECT isbn, title, price, stock, aisle, bin FROM purchase_books'
    cur.execute(query)
    books = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('purchase_books.html', books=books)

@app.route('/rental_books')
def rental_books():
    conn = get_db_connection()
    cur = conn.cursor()
    query = 'SELECT isbn, title, aisle, bin FROM rental_books'
    cur.execute(query)
    books = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('rental_books.html', books=books)

@app.route('/member_info', methods=['GET'])
def member_info():
    uid = request.args.get('uid')
    member_info = None
    member_not_found = False

    if uid:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT name, rental_count, rented_books, purchase_count
            FROM member_info
            WHERE id = %s
        ''', (uid,))
        result = cur.fetchone()

        if result:
            member_info = {
                'name': result[0],
                'rental_count': result[1],
                'rented_books': result[2],
                'purchase_count': result[3]
            }
        else:
            member_not_found = True

        cur.close()
        conn.close()

    return render_template('member_info.html', member_info=member_info, member_not_found=member_not_found)


@app.route('/books_due', methods=['GET', 'POST'])
def books_due():
    books_due = []
    date_not_found = False

    if request.method == 'POST':
        due_date = request.form.get('due_date')

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT member_id, member_name, title 
                FROM rental_transactions
                WHERE return_date = %s
            ''', (due_date,))
            books_due = cur.fetchall()

            if not books_due:
                date_not_found = True

            cur.close()
            conn.close()
        except Exception as e:
            date_not_found = True

    return render_template('books_due.html', books_due=books_due, date_not_found=date_not_found)


@app.route('/books_by_price', methods=['GET', 'POST'])
def books_by_price():
    books = []
    price_not_found = False

    if request.method == 'POST':
        max_price = request.form.get('max_price')

        try:
            max_price = float(max_price)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT isbn, title, price, stock, aisle, bin
                FROM purchase_books
                WHERE price <= %s
            ''', (max_price,))
            books = cur.fetchall()

            if not books:
                price_not_found = True

            cur.close()
            conn.close()
        except ValueError:
            price_not_found = True

    return render_template('books_by_price.html', books=books, price_not_found=price_not_found)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute('''
                INSERT INTO available_books (isbn, title, author, genre)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (isbn) DO NOTHING
            ''', (isbn, title, author, genre))
            conn.commit()
            return redirect('/available_books')

        except Exception as e:
            conn.rollback()
            return f"An error occurred: {str(e)}", 500
        finally:
            cur.close()
            conn.close()

    return render_template('add_book.html')



@app.route('/update_price', methods=['GET', 'POST'])
def update_price():
    if request.method == 'POST':
        title = request.form.get('title')
        new_price = request.form.get('price')

        if not title or not new_price:
            return "Title or Price cannot be empty. Please provide valid inputs."

        try:
            new_price = float(new_price)
        except ValueError:
            return "Invalid price. Please enter a numeric value."

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE purchase_books
            SET price = %s
            WHERE title = %s
        ''', (new_price, title))
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/purchase_books')

    return render_template('update_price.html')

@app.route('/update_stock', methods=['GET', 'POST'])
def update_stock():
    if request.method == 'POST':
        title = request.form.get('title')
        new_stock = request.form.get('stock')

        if not title or not new_stock:
            return "Title or stock cannot be empty. Please provide valid inputs."

        try:
            new_stock = int(new_stock)
        except ValueError:
            return "Invalid stock. Please enter a numeric value."

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('CALL update_stock(%s, %s)', (title, new_stock))
            conn.commit()
        except Exception as e:
            return f"An error occurred: {e}", 500
        finally:
            cur.close()
            conn.close()

        return redirect('/purchase_books')

    return render_template('update_stock.html')


@app.route('/delete_book', methods=['GET', 'POST'])
def delete_book():
    if request.method == 'POST':
        title = request.form.get('title')

        if not title:
            return "Title cannot be empty. Please provide a valid title."

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('CALL delete_book(%s)', (title,))
            conn.commit()
        except Exception as e:
            return f"An error occurred: {e}", 500
        finally:
            cur.close()
            conn.close()

        return redirect('/available_books')

    return render_template('delete_books.html')


if __name__ == '__main__':
    app.run(debug=True)

