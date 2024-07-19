from flask import Flask, render_template,request, session, logging, redirect, url_for, flash
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Lokesh@12'
app.config['MYSQL_DB'] = 'flask_loki'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def default():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    res = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if res > 0: 
        return render_template('articles.html', articles = articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg = msg)
    cur.close()

    return render_template('dashboard.html')

@app.route('/articles/<int:id>')
def article(id):
    cur = mysql.connection.cursor()
    res = cur.execute('select * from articles where id = %s', [id])
    article = cur.fetchone()
    if res > 0:
        return render_template('article.html', article = article)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min = 1, max = 50)])
    username = StringField('Username', [validators.Length(min = 4, max = 25)])
    email = StringField('Emial', [validators.Length(min = 6, max = 50)])
    password = PasswordField('Password', [validators.DataRequired(),validators.EqualTo('confirm', message="Password doesn't matched")])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods = ['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, username, email, password) VALUES(%s, %s, %s, %s)",(name, username, email, password))
        mysql.connection.commit()
        cur.close()
        flash("You're registered Now Login", 'success')

        return render_template('register.html', form = form)
    return render_template('register.html', form = form)    

@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        res = cur.execute("SELECT * FROM users where username = %s",[username])
        if res > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True 
                session['username'] = username
                flash("You're logged In successfully",'success')
                return render_template('dashboard.html')  
            else:
                error = 'Invalid Password'
                return render_template('login.html', error = error)
            cur.close()
        else:
            error = 'User Notfound'
            return render_template('login.html', error = error)
    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized User, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap 

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You're Now logged out", 'success')
    return redirect(url_for(('login')))

@app.route('/edit_article/<int:id>', methods = ['GET', 'POST'])
@is_logged_in
def edit_articles(id):
    cur = mysql.connection.cursor()
    res = cur.execute('select * from articles where id = %s',[id])
    article = cur.fetchone()
    form=ArticleForm(request.form)
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']
        cur=mysql.connection.cursor()
        cur.execute('update articles set title=%s, body = %s where id = %s',(title,body,id))
        mysql.connection.commit()
        cur.close()
        flash('Article Updated','success')
        return redirect(url_for('dashboard'))   
    return render_template('edit_article.html',form=form)

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    res = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if res > 0: 
        return render_template('dashboard.html', articles = articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg = msg)
    cur.close()

    return render_template('dashboard.html')

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min = 1, max = 50)])
    body = TextAreaField('Body', [validators.Length(min = 4)])

@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data
        cur=mysql.connection.cursor()
        cur.execute('INSERT INTO articles(title,body,author) values(%s,%s,%s)',(title, body,session['username']))
        mysql.connection.commit()
        cur.close()
        flash('Article Created','success')
        return redirect(url_for('dashboard'))   
    return render_template('add_article.html',form=form)

@app.route('/delete_article/<int:id>', methods = ['POST'])
def delete_article(id):
    cur = mysql.connection.cursor()
    res = cur.execute('delete from articles where id = %s', [id])
    mysql.connection.commit()
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key = "lokesh@12"
    app.run(debug=True)