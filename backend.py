from flask import Flask
from flask import render_template , redirect , flash , url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from wtforms.validators import DataRequired, Regexp, ValidationError, Email,Length, EqualTo
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from functools import wraps


#Kullanıcı girişi dekoratörü
#Doğrudan url üzerinden erişimi kapatmak için
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın" , "danger")
            return redirect(url_for("login"))
    return decorated_function


#Kullanıcı giriş formu bilgilerinin alınması
class LoginForm(Form):
    username = StringField("Kullanıcı Adı : ")
    password = PasswordField("Parola")


#Kullanıcı kayıt formu classı
class RegisterForm(Form):
    name = StringField("İsim Soyisim" , validators=[validators.length(min = 4 , max =30),validators.DataRequired])
    username = StringField("Kullanıcı Adı" , validators=[validators.length(min = 6 , max =25),validators.DataRequired])
    email = StringField("Email adresi" , validators=[validators.DataRequired , validators.Email(message = " Lütfen Geçerli bir Email Adresi Giriniz")])
    password = PasswordField('Parola', validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm", message="parola uyuşmuyor")
    ])
    confirm = PasswordField("Parolayı Yeniden Gir")

#Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.Length(min = 5, max=100)])
    content = TextAreaField("Makale İçeriği" , validators=[validators.Length(min=10)])




#Flask app oluşturma
app = Flask(__name__)
app.secret_key = "EBB"
#Flask app database ayarları
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "projects"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)  #Uygulamaya entegre ettirilmesi




@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")


@app.route('/')
def index():
    return render_template("index.html")



@app.route("/about")
def about():
    return render_template("about.html")

#register olma
#Kayıt olma formu
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST":
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES (%s,%s,%s,%s) "
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("Succesfull ..." , "success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html" , form = form)
        

#Kullanıcı giriş kısmı
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        passwpord_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result>0 :
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(passwpord_entered,real_password):
                flash("Giriş Başarılı " , "success")

                session["logged_in"] = True
                session["username"] = username


                return redirect(url_for("index"))
            else:
                flash("Parola yanlış !!!" , "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı !!! ", "danger")
            return redirect(url_for("login"))


    return render_template("login.html" , form = form)

#Makale Kısmı
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)
    
    if result>0 :
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")


#Çıkış yapma kısmı
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#Makale Ekleme 
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()

        cursor.close()

        flash("Makale başarıyla eklendi","success")
        return redirect(url_for("dashboard"))
    


    return render_template("addarticles.html",form = form)

 
#Uygulama kontrol
if __name__ == "__main__":
    app.run(debug=True)

