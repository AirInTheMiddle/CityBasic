from flask import Flask, request, redirect, url_for, render_template, flash, session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import random
import string
from datetime import datetime, timedelta, timezone
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MySQL configurations
app.config['MYSQL_HOST'] = '172.17.0.2'
app.config['MYSQL_USER'] = 'camas_city_db_admin'
app.config['MYSQL_PASSWORD'] = 'testpassword'
app.config['MYSQL_DB'] = 'camas_city'

mysql = MySQL(app)

# Email configurations
app.config['MAIL_SERVER'] = 'smtp.office365.com'  # or 'smtpout.secureserver.net' for GoDaddy
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'thomas@airinthemiddle.com'
app.config['MAIL_PASSWORD'] = 'kqy@mxh8VMF!rtq4yqw'  # Replace with your email password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'thomas@airinthemiddle.com'

mail = Mail(app)

# Routes and logic
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        code = ''.join(random.choices(string.digits, k=6))
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=10)

        cursor = mysql.connection.cursor()
        print(f'Inserting code {code} for email {email} with expiration {expiration_time}')
        cursor.execute("INSERT INTO login_codes (email, code, expiration_time) VALUES (%s, %s, %s)", (email, code, expiration_time))
        mysql.connection.commit()
        cursor.close()

        msg = Message('Your Login Code', sender='thomas@airinthemiddle.com', recipients=[email])
        msg.body = f'Your login code is {code}. It will expire in 10 minutes.'
        try:
            mail.send(msg)
            print(f'Email sent to {email} with code {code}')
            flash('A login code has been sent to your email.')
        except Exception as e:
            print(f'Failed to send email: {str(e)}')
            app.logger.error(f'Failed to send email: {str(e)}')
            flash('Failed to send email. Please try again.')

        return redirect(url_for('verify', email=email))
    return render_template('index.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    email = request.args.get('email')
    if request.method == 'POST':
        code = request.form['code']
        print(f'Received verification request for email {email} with code {code}')
        current_time = datetime.now(timezone.utc)
        print(f'Current time: {current_time}')

        cursor = mysql.connection.cursor()
        print(f"Executing query: SELECT * FROM login_codes WHERE email='{email}' AND code='{code}' AND expiration_time > '{current_time}'")
        cursor.execute("SELECT * FROM login_codes WHERE email=%s AND code=%s AND expiration_time > %s", (email, code, current_time))
        result = cursor.fetchone()
        print(f'Query result: {result}')
        if result:
            print(f'Code {code} for {email} is valid. Result: {result}')
            session['email'] = email
            cursor.execute("DELETE FROM login_codes WHERE email=%s", [email])
            mysql.connection.commit()
            cursor.close()
            print(f'Code verified for {email}, redirecting to profile')
            return redirect(url_for('profile'))
        else:
            print(f'Code {code} for {email} is invalid or expired')
            cursor.close()
            flash('Invalid or expired code. Please try again.')
            return redirect(url_for('index'))
    return render_template('verify.html', email=email)

@app.route('/profile')
def profile():
    if 'email' not in session:
        print('No email in session, redirecting to index')
        return redirect(url_for('index'))

    email = session['email']
    print(f'Logged in as {email}, displaying profile')
    # Display dummy user profile
    return render_template('profile.html', email=email)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010)