from flask import Flask, request, jsonify
import sqlite3
import os

# Init app
app = Flask(__name__)

# 👇 Add your trap listener IP here
TRAP_LISTENER_IP = "192.168.31.13"  # <-- Important! Replace this with your public IP


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/', methods=['GET'])
def home():
    return "<h1>Distant Reading Archive</h1><p>This is a prototype API</p>"


@app.route('/api/v2/resources/books/all', methods=['GET'])
def api_all():
    db_path = os.path.join('db', 'books.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_books = cur.execute('SELECT * FROM books;').fetchall()
    return jsonify(all_books)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found</p>", 404


@app.route('/api/v2/resources/books', methods=['GET'])
def api_filter():
    query_parameters = request.args
    id = query_parameters.get('id')
    published = query_parameters.get('published')
    author = query_parameters.get('author')

    query = 'SELECT * FROM books WHERE'
    to_filter = []

    if id:
        query += ' id=? AND'
        to_filter.append(id)
    if published:
        query += ' published=? AND'
        to_filter.append(published)
    if author:
        query += ' author=? AND'
        to_filter.append(author)

    if not (id or published or author):
        return page_not_found(404)

    query = query[:-4] + ';'

    db_path = os.path.join('db', 'books.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()
    return jsonify(results)


@app.route('/api/v2/resources/books', methods=['POST'])
def add_book():
    if not request.is_json:
        return "<p>The content isn't of type JSON</p>"

    content = request.get_json()
    title = content.get('title')
    author = content.get('author')
    published = content.get('published')
    first_sentence = content.get('first_sentence')

    db_path = os.path.join('db', 'books.db')
    conn = sqlite3.connect(db_path)
    query = f'INSERT INTO books (title, author, published, first_sentence) \
              VALUES ("{title}", "{author}", "{published}", "{first_sentence}");'

    cur = conn.cursor()
    cur.execute(query)
    conn.commit()

    return jsonify(request.get_json())


# Trap endpoints with IP checking 👇

@app.route('/admin')
def trap_admin():
    if request.remote_addr != TRAP_LISTENER_IP:
     return jsonify({"msg": "Accessed /admin trap successfully"}), 200


@app.route('/debug')
def trap_debug():
    if request.remote_addr != TRAP_LISTENER_IP:
      return jsonify({"msg": "Accessed /debug trap successfully"}), 200
    return jsonify({"trap": "Debugging access attempt detected"}), 403


@app.route('/config')
def trap_config():
    if request.remote_addr != TRAP_LISTENER_IP:
        return jsonify({"trap": "Sensitive config access blocked"}), 403
    return jsonify({"msg": "Accessed /config trap successfully"}), 200


@app.route('/internal')
def trap_internal():
    if request.remote_addr != TRAP_LISTENER_IP:
        return jsonify({"trap": "Attempted access to internal API"}), 403
    return jsonify({"msg": "Accessed /internal trap successfully"}), 200


@app.route('/logs')
def trap_logs():
    if request.remote_addr != TRAP_LISTENER_IP:
       return jsonify({"msg": "Accessed /logs trap successfully"}), 200
    return jsonify({"trap": "Log file access forbidden"}), 403

if __name__ == "__main__":
    app.run(debug=False, threaded=True, port=5000)
