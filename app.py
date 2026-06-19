from flask import Flask, flash, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from flask_mail import Mail, Message    

# Create Flask app FIRST
app = Flask(__name__)
app.secret_key = "notes123"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'r.snehareddy04@gmail.com'
app.config['MAIL_PASSWORD'] = 'kdfh pqdl tfpp kret'

mail = Mail(app)

# Database Connection
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",       
        password="root",       
        database="notesdb"
    )
    return conn

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/viewall')
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        
        if not username or not email or not password:
            flash("Please fill all fields.", "danger")
            return redirect('/register')

        # Hash the password before saving
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if username already exists
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cur.fetchone()
        if exists:
            # Close connection and inform user
            cur.close()
            conn.close()
            flash("Username already taken. Choose another.", "danger")
            return redirect('/register')

        # Insert new user into users table
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()

        flash("Registration successful! You can now log in.", "success")
        return redirect('/login')

    # If GET -> show registration form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If POST -> authenticate
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        # Basic check
        if not username or not password:
            flash("Please enter username and password.", "danger")
            return redirect('/login')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        # Check whether user exists and password matches
        if user and check_password_hash(user['password'], password):
            # Save user id and username in session for future access control
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome, {user['username']}!", "success")
            return redirect('/viewall')
        else:
            flash("Invalid username or password.", "danger")
            return redirect('/login')

    # If GET -> show login page
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session data
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')

@app.route('/addnote', methods=['GET', 'POST'])
def addnote():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        user_id = session['user_id']

        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect('/addnote')

        conn = get_db_connection()
        cur = conn.cursor()
        # Save note with user_id to keep notes private
        cur.execute("INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s)",
                    (title, content, user_id))
        conn.commit()
        cur.close()
        conn.close()

        flash("Note added successfully.", "success")
        return redirect('/viewall')

    # GET -> show add note form
    return render_template('addnote.html')

@app.route('/viewall')
def viewall():
    # Ensure user logged in
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # Fetch only notes that belong to this user
    cur.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    notes = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('viewnotes.html', notes=notes)

@app.route('/viewnotes/<int:note_id>')
def viewnotes(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # Select note only if it belongs to current user
    cur.execute("SELECT id, title, content, created_at FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    note = cur.fetchone()
    cur.close()
    conn.close()

    if not note:
        # Either note doesn't exist or doesn't belong to the user
        flash("You don't have access to this note.", "danger")
        return redirect('/viewall')

    return render_template('singlenote.html', note=note)

@app.route('/updatenote/<int:note_id>', methods=['GET', 'POST'])
def updatenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Check existence and ownership
    cur.execute("SELECT id, title, content FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    note = cur.fetchone()

    if not note:
        cur.close()
        conn.close()
        flash("You are not authorized to edit this note.", "danger")
        return redirect('/viewall')

    if request.method == 'POST':
        # Get updated data
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect(url_for('updatenote', note_id=note_id))

        # Update query guarded by user_id
        cur.execute("UPDATE notes SET title = %s, content = %s WHERE id = %s AND user_id = %s",
                    (title, content, note_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Note updated successfully.", "success")
        return redirect('/viewall')

    # If GET -> render update form with existing note data
    cur.close()
    conn.close()
    return render_template('updatenote.html', note=note)


@app.route('/deletenote/<int:note_id>', methods=['POST'])
def deletenote(note_id):
    # This route expects a POST request (safer than GET for delete)
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Delete only if the note belongs to the current user
    cur.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    flash("Note deleted.", "info")
    return redirect('/viewall')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        message = request.form['message']

        msg = Message(
            subject="New Contact Form Message",
            sender=app.config['MAIL_USERNAME'],
            recipients=['r.snehareddy04@gmail.com']  # Your email
        )

        msg.body = f"""
New Contact Form Submission

Username: {username}
Email: {email}

Message:
{message}
"""

        mail.send(msg)

        flash("Message sent successfully!", "success")
        return redirect('/contact')

    return render_template('contact.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgotpassword.html')


# --------------------
# Send Reset Link Route
# --------------------
@app.route('/send_reset_link', methods=['POST'])
def send_reset_link():

    email = request.form['email']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    user = cursor.fetchone()

    if user:

        reset_link = f"http://127.0.0.1:5000/reset_password/{email}"

        msg = Message(
            "Password Reset Request",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        msg.body = f"""
Hello {user['username']},

Click the link below to reset your password:

{reset_link}

If you did not request this password reset, please ignore this email.
"""

        mail.send(msg)

        cursor.close()
        conn.close()

        flash("Password reset link sent to your email.", "success")
        return redirect('/login')

    cursor.close()
    conn.close()

    flash("Email not found.", "danger")
    return redirect('/forgot_password')



@app.route('/reset_password/<email>', methods=['GET', 'POST'])
def reset_password(email):

    if request.method == 'POST':

        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (hashed_password, email)
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Password updated successfully. Please login.", "success")
        return redirect('/login')

    return render_template(
        'resetpassword.html',
        email=email
    )

@app.route('/dashboard')
def Dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

if __name__ == '__main__':
    
    app.run(debug=True)