from flask import Flask, request, session, render_template, redirect, flash
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key"

connectionString = "mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false"
client = pymongo.MongoClient(connectionString)
db = client['inotebook-flask']
usersCollection = db.users
notesCollection = db.notes

# Function to create user
def insertUser(name, username, password):
    user = {
        "name": name,
        "username": username,
        "password": generate_password_hash(password, method="sha256"),
        "created": datetime.now()
    }
    usersCollection.insert_one(user)

# Function to create note
def insertNote(title, description, user):
    chars = string.ascii_lowercase + string.digits
    size = 8
    note = {
        "title": title,
        "description": description,
        "user": user,
        "noteID": ''.join(random.choice(chars) for __ in range(size)),
        "created": datetime.now()
    }
    notesCollection.insert_one(note)

# Function to update note
def updateNote(title, description, noteID):
    note = {"noteID": noteID}
    setValues = {"$set": {"title": title, "description": description}}
    notesCollection.update_one(note, setValues)

# Function to delete note
def deleteNote(noteID):
    notesCollection.delete_one({"noteID": noteID})

# API Routes First
@app.route("/handlesignup", methods=["GET", "POST"])
def handlesignup():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")

        userExists = usersCollection.find_one({"username": username})

        if not name or not username or not password or not cpassword:
            flash("Please fill up your signup credentials", "error")
            return redirect("/")

        elif len(username) < 4 or len(username) > 12:
            flash("Username must contain characters between 4 to 12!", "error")
            return redirect("/")

        elif not username.isalnum() or username.isalpha() or username.isnumeric():
            flash("Username must contain only alphanuemric characters!", "error")
            return redirect("/")

        elif userExists:
            flash("This user already exists!", "error")
            return redirect("/")

        elif len(password) < 8:
            flash("Password must contain atleast 8 characters!", "error")
            return redirect("/")

        elif password.isalnum() or password.isalpha() or password.isnumeric():
            flash("Please choose a strong password!", "error")
            return redirect("/")

        elif password!= cpassword:
            flash("Password and cofirm password do not match!", "error")
            return redirect("/")

        else:
            insertUser(name, username, password)
            flash("Your user account has been successfully created!", "success")
            return redirect("/login")
    else:
        return "(400) Bad Request"

@app.route("/handlelogin", methods=["GET", "POST"])
def handlelogin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = usersCollection.find_one({"username": username})

        if not username or not password:
            flash("Please fill your login details!", "error")
            return redirect("/login")

        elif not user or not check_password_hash(user['password'], password):
            flash("Invalid credentials! Please try again.", "error")
            return redirect("/login")

        else:
            session['user'] = username
            flash("You have been successfully loggedin!", "success")
            return redirect("/")
    else:
        return "(400) Bad Request"

@app.route("/logout", methods=["GET", "POST"])
def logout():
    if 'user' in session:
        session.pop('user')
        flash("You have been successfully loggedout!", "success")
        return redirect(request.path)
    else:
        return redirect("/login")

@app.route("/addnote", methods=["GET", "POST"])
def addnote():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        user = session['user']

        if not title or not description:
            flash("Please fill the details of your note!", "error")
            return redirect("/")

        elif len(title) < 10 or len(description) < 10:
            flash("Title or description cannot be under 10 characters!", "error")
            return redirect("/")
        
        else:
            insertNote(title, description, user)
            flash("Your note has been added successfully!", "success")
            return redirect("/")
    else:
        return "(400) Bad Request"

@app.route("/updatenote/<string:noteID>", methods=["GET", "POST"])
def updatenote(noteID):
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        currentUser = session['user']

        note = notesCollection.find_one({"noteID": noteID})

        if not title or not description:
            flash("Please fill the details of your note!", "error")
            redirect("/edit/{}".format(note['noteID']))

        elif len(title) < 10 or len(description) < 10:
            flash("Title or description cannot be under 10 characters!", "error")
            redirect("/edit/{}".format(note['noteID']))

        else:
            updateNote(title, description, noteID)
            flash("Your note has been updated successfully!", "success")
            return redirect("/edit/{}".format(note['noteID']))
    else:
        return "(400) Bad Request"

@app.route("/delete/<string:noteID>")
def deletenote(noteID):
    if 'user' in session:
        currentUser = session['user']

        note = notesCollection.find_one({"noteID": noteID})

        if note['user'] != currentUser:
            flash("You cannot delete other user's notes!", "error")
            return redirect("/")
        else:
            deleteNote(noteID)
            flash("Your note has been deleted successfully!", "success")
            return redirect("/")
    else:
        return "(400) Bad Request"

# Then, Frontend 
@app.route("/")
def home():
    if 'user' in session:
        notes = notesCollection.find({})
        return render_template("index.html", notes=notes)
    else:
        return redirect("/login")

@app.route("/register")
def register():
    if 'user' in session:
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login")
def login():
    if 'user' in session:
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/edit/<string:noteID>")
def edit(noteID):
    if 'user' in session:
        currentUser = session['user']
        note = notesCollection.find_one({"noteID": noteID})

        if currentUser != note['user']:
            flash("You cannot edit other user's note! Access forbidden", "error")
            return redirect("/")
        else:
            return render_template('edit.html', note=note)
    else:
        return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)