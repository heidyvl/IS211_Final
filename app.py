from flask import Flask, render_template, request, g, redirect, session, url_for, escape, abort, flash
import re
import sqlite3
from contextlib import closing

DATABASE = 'blogging.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'password'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)

@app.route('/logout', methods=['POST'])
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if session['logged_in'] != True:
        flash("You are not logged in")
        return redirect('/login')
    else:
        cur = g.db.execute('select id, date, title, content from post order by date desc')
        posts = [dict(id=row[0], date=row[1], title=row[2], content=row[3]) for row in cur.fetchall()]
        
        return render_template('dashboard.html', posts=posts)

@app.route('/post/add', methods=['POST', 'GET'])
def add_post():
    if session['logged_in'] != True:
        flash("You are not logged in")
        return redirect('/login')
    else:
        if request.method == 'GET':
            return render_template('add_post.html')
        if request.method=='POST':
            title=request.form['title']
            date=request.form['date']
            author = request.form['author']
            content =  request.form['content']
            query="INSERT INTO post(title,date, author, content ) VALUES(?,?,?,?)"
            g.db.execute(query,(title,date, author,content))
            g.db.commit()
            flash('New entry was successfully posted')
            return redirect(url_for('dashboard'))

@app.route('/post/delete/<id>', methods=['GET'])
def delete_post(id):
    if session['logged_in'] != True:
        flash("You are not logged in")
        return redirect('/login')
    else:
        if request.method == 'GET':
           
            g.db.execute('DELETE FROM post where id = ?', (id,))
            g.db.commit()
            
            return redirect(url_for('dashboard'))

@app.route('/post/edit/<id>', methods=['GET', 'POST'])
def edit_post(id):
    if session['logged_in'] != True:
        flash("You are not logged in")
        return redirect('/login')
    else:
        if request.method == 'GET':
            cur = g.db.execute('select id, date, title, content from post WHERE id = ?', (id,))
            posts = [dict(id=row[0], date=row[1], title=row[2], content=row[3]) for row in cur.fetchall()]
            return render_template('edit_post.html', id=id, posts=posts)
        if request.method=='POST':
            title = request.form['title']
            date=request.form['date']
            author = request.form['author']
            content =  request.form['content']
            query=('UPDATE post SET title=?,date=?, author=?, content=? WHERE id = ?')
            g.db.execute(query, (title,date, author,content, id))
            g.db.commit()
            return  redirect(url_for('dashboard'))



   
# set the secret key.  keep this really secret: 
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == '__main__':
    app.run()
