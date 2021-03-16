from MySQLdb.cursors import Cursor
from flask import Flask ,render_template, flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,ValidationError
from wtforms.validators import InputRequired, Email, email_validator
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı kayıt formu

class RegisterForm(Form):
    name = StringField("Name Surname", validators=[validators.length(min=5, max=25)])
    username = StringField("Username", validators=[validators.length(min=5, max=25)]) 
    email = EmailField("E-mail", validators=[validators.Email(message="Please enter a viable e-mail")])
    password = PasswordField("Password ",validators=[
        validators.DataRequired("Please determine a password"),
        validators.equal_to(fieldname="confirm", message="Password is not get numb")
    ])
    confirm = PasswordField("Correct password")

#Kullanıcı giriş formu

class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

#Article Formu

class ArticleForm(Form):
    title = StringField("Blog Title")
    content = TextAreaField("Blog Content")

#Giriş kontrol decoraterı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
           return f(*args, **kwargs)
        else:
           flash("Bu sayfayı görebilmek için lütfen giriş yapınız...","danger")
           return redirect(url_for("login")) 
    return decorated_function
    

app = Flask(__name__)

app.secret_key = "myblog" #flash kullanmak için sifre olusturduk

#mysql bağlantısını yapmak için yazmamız gereknler dokumantasyondan bakılır
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "myblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app) #flask ile mysql ilişkisi kuruldu

@app.route("/")
def mainpage():
    return redirect(url_for("home"))

#Ana sayfa
@app.route("/home")
def home():
    
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("home.html",articles = articles)
    else:
        return render_template("home.html")

    

@app.route("/blog", methods = ["GET","POST"])
@login_required
def blog():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Successfuly Added! ","success")
        return redirect(url_for("blog"))
    else:
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where author=%s "
        result = cursor.execute(sorgu,(session["username"],))
        if result > 0:
            articles = cursor.fetchall()
            return render_template("blog.html", articles=articles,form = form)
        else:
            return render_template("blog.html",form = form)

#blog yazısı silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()
    #böyle bir article var mı
    sorgu = "Select * from articles where author=%s and id=%s"
    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:

        sorgu2 = "Delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("blog"))
    else:
        flash("Can not be found like this ","danger")
        return redirect(url_for("blog"))

#Blog yazısı guncelleme
@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where author=%s and id=%s"
        result = cursor.execute(sorgu,(session["username"],id))
        
        if result == 0 :
            flash("Can not be found like this text or can not access","danger")
            return redirect(url_for("blog"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html",form=form)
    else:

        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        cursor = mysql.connection.cursor()
        sorgu2 = "Update articles Set title =%s , content=%s where id=%s "

        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Blog is updated successfuly!","success")
        return redirect(url_for("blog"))
#blog yazısı detay görme
@app.route("/detail/<string:id>")
def detail(id):
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id=%s"

        result = cursor.execute(sorgu,(id,))

        if result > 0:
            article = cursor.fetchone()
            
            return render_template("detail.html",article = article)
        else:
            flash("Can't be found this like text")
            return redirect(url_for("home"))
    


    

#Hakkımda sayfası
@app.route("/about")
def about():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from users"
    result = cursor.execute(sorgu)
    if result > 0:
        users = cursor.fetchall()
        return render_template("about.html", users = users)
    else:
        flash("This page is just not prepare")
        return render_template("about.html")



    

#Giriş Yap
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data #formdan username ve şifre alınır atanır
        password = form.password.data

        cursor = mysql.connection.cursor() #sql çalıştırır

        sorgu = "Select * from users where username = %s" #kullanıcıları sorgularız
        result = cursor.execute(sorgu,(username,)) #sorgu çalışır ve girilen kullanıcı varsa gelir

        if result > 0: #eğer böyle bir kullancı varsa
            data = cursor.fetchone() #kullanıcı bilgisi alınır
            real_password = data["password"] #databasedki şifre alınır

            if sha256_crypt.verify(password,real_password): #girilen şifreyle datadaki şifre aynıysa 
                flash("Successful entered","success")
                #session belirle giriş yapıldığında true olur
                session["logged_in"] = True #giriş yapıldıgında session true olur
                session["username"] = username #giriş yapılan kullanıcı adımız
                return redirect(url_for("home"))
            else:
                flash("Incorrect password","danger")
                return redirect(url_for("login"))
        else: # böyle bir kullanıcı yoksa
            flash("Not found like this user","danger")
            return redirect(url_for("login"))
    else: 
        return render_template("login.html", form = form) #istek get ise oluşturulan formu sayfaya göndeririz

#Kayıt ol
@app.route("/register", methods=["GET","POST"])
def register():

    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        #kayıt olma işlemi
        #forma yazılan bilgileri alırız
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) #şifreleyerek kaydeder

        cursor = mysql.connection.cursor()
        #veritabanına ekleme işlemi
        sorgu = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        #sorguyu çalıştırırız alınan değerleri veritabanına yollarız
        cursor.execute(sorgu,(name,username,email,password))

        mysql.connection.commit()
        cursor.close()
        flash("Signed up!","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
#Çıkış yap
@app.route("/logout")
def logout():
    #session logged_in i temizler 
    session.clear()
    return redirect(url_for("home"))

    


    
    
    






 


if __name__ == "__main__":
    app.run(debug=True)