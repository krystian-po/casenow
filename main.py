from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import datetime
import random
import hashlib


casenow = Flask(__name__)
casenow.secret_key = "seventeen"
### Logging function that fills up the casenow.txt file ###
def logger(message):
    now = datetime.datetime.now()
    nowtime = now.strftime(f'%d.%m.%Y %H:%M')
    username = session.get('username', 'Unknown')

    with open('casenow.txt', 'a') as casenowlog:
        casenowlog.write(f'<{nowtime}> {username} {message}\n')

### Connecting to the MySQL database ###
def dbconnectiontest():
    try:
        connection = mysql.connector.connect(
            host = "127.0.0.1",
            user = "root",
            password = "password",
            database = "casenowdb")
        return connection

    except mysql.connector.Error as error:
        print(f'Error: {error}')
        return None

### Main login page logic ###
@casenow.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session["username"] = username

        # Grabs user data for username, password check
        connection = dbconnectiontest()
        if connection:
            cursor = connection.cursor()
            query = "SELECT * FROM logins WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            # Comparing hashed input to database
            if user:
                dbpassword = user[1]
                hashed = hashlib.sha256(password.encode()).hexdigest()

                if hashed == dbpassword:
                    session['user_id'] = user[0]
                    session['user_role'] = user[2]
                    print(session['user_role'])
                    logger('logged in')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid username or password.'
                    logger('attempted to log in.')
                    return render_template('login.html', error=error)
            else:
                error = 'Invalid username or password.'
                logger('attempted to log in.')
                return render_template('login.html', error=error)

        return render_template('login.html')

    return render_template('login.html')

### Register page logic ###
@casenow.route('/register', methods=['GET', 'POST'])
def register ():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        check_pass = request.form.get('password_confirm')
        role_key = request.form.get('role_key')
        now = datetime.datetime.now()
        nowtime = now.strftime(f'%d.%m.%Y %H:%M')
        print(username, password, check_pass, role_key, nowtime)

        # Validation that username is atleast 4 characters long
        if not username or len(username) < 4:
            flash("Username needs to be atleast 4 characters long.", "error")
            return redirect(url_for("register"))
        
        # Validation that password is atleast 8 characters long
        if not password or len(password) < 8:
            flash("Password needs to be atleast 8 characters long.", "error")
            return redirect(url_for("register"))
        
        # Validation that password and confirm password matches
        if password != check_pass:
                flash("Passwords do not match, try again.", "error")
                return redirect(url_for('register'))

        # Hashing password with SHA256
        hashed = hashlib.sha256(password.encode()).hexdigest()

        # Checking for role key to assign role to user
        if role_key == "ae1ksp":
            role = "admin"
        elif role_key == "qz9mjf":
            role = "engineer"
        else:
            role = "customer"
        
        # Grab login data for user
        connection = dbconnectiontest()
        if connection:
                cursor = connection.cursor()
                try:
                    query = "SELECT * FROM logins WHERE username = %s"
                    cursor.execute(query, (username,))
                    existing_user = cursor.fetchone()
                    if existing_user:
                        flash('Username already exists', 'error')
                        return redirect(url_for('register'))
                    else:
                        # Insert new user into database
                        insert_query = "INSERT INTO logins (username, userpass, usertype, datecreated) VALUES (%s, %s, %s, %s)"
                        cursor.execute(insert_query, (username, hashed, role, nowtime))
                        connection.commit()
                        return redirect(url_for('login'))
                except mysql.connector.Error as error:
                    flash(f'An error occurred: {error}', 'error')
                finally:
                    cursor.close()
                    connection.close()
        else:
            flash('Could not connect to the database.', 'error')

    return render_template('register.html')

### Dashboard logic
@casenow.route('/dashboard')
def dashboard():

    # Connection timeout
    if 'user_id' in session:
        user_id = session['user_id']
        return render_template('dashboard.html', user_id=user_id)
    else:
        return redirect(url_for('login'))

### My Cases logic
@casenow.route('/mycases')
def mycases():

    # Grabs previously stored username and user_role variable
    connection = dbconnectiontest()
    username = session.get("username", None)
    user_role = session.get("user_role", None)

    if connection:
        cursor = connection.cursor(dictionary=True)
        if 'user_id' in session:
            user_id = session['user_id']
            user_role = session['user_role']
            ### If the user role is admin they can see all cases
            if user_role == "admin":
                cursor.execute("SELECT * FROM cases")
            else:
            ### If user role is not admin they can only see cases under their name
                cursor.execute("SELECT * FROM cases WHERE username = %s OR assigned_engineer = %s", (username, username))
        
        cases = cursor.fetchall()
        connection.close()

    ### Connection timeout
    if 'user_id' in session:
        user_id = session['user_id']
        return render_template('mycases.html', user_id=user_id, cases=cases)
    else:
        return redirect(url_for('login'))

### Logic for submitting and logging case comments
@casenow.route('/case/<int:caseid>/submit_comment', methods=['POST'])
def submit_comment(caseid):
    new_comment = request.form['new_comment'].strip()
    now = datetime.datetime.now()
    nowtime = now.strftime(f'%d.%m.%Y %H:%M')

    # Data validation to not allow empty comments to be submitted
    if not new_comment:
        flash('Please enter a comment.', 'error')
        return redirect(url_for('cases', caseid=caseid))
    try:
        connection = dbconnectiontest()
        if connection:
            cursor = connection.cursor()
            # Grab any previous comments
            cursor.execute("SELECT comments FROM cases WHERE caseid = %s", (caseid,))
            existing_comments = cursor.fetchone()[0]  # Fetch the first row and first column value
            # Connection timeout
            username = session.get("username", None)
            if username is None:
                flash("Username timed out", "error")
                return redirect(url_for('login'))
            print(username)

            # Adds new comment to previous comments to form total comments
            if existing_comments:
                updated_comments = f"{existing_comments}\n{nowtime} <{username}>: {new_comment}"

            else:
                updated_comments = f"{nowtime} <{username}>: {new_comment}"

            # Updates the database with new comments
            query = "UPDATE cases SET comments = %s WHERE caseid = %s"
            cursor.execute(query, (updated_comments, caseid))
            connection.commit()
            print(updated_comments)
            print(existing_comments)

            flash('Comment added successfully.', 'success')

            cursor.close()
            connection.close()

    except mysql.connector.Error as error:
        flash(f'An error occurred: {error}', 'error')

    return redirect(url_for('cases', caseid=caseid))

### Logic for closing cases
@casenow.route('/close_case/<int:caseid>', methods=['POST'])
def close_case(caseid):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # If the user role is either engineer or admin they can close cases
    user_role = session.get('user_role')
    if user_role in ['engineer', 'admin']:
        connection = dbconnectiontest()
        if connection:
            cursor = connection.cursor()
            try:

                # Changes the status of specific case to Closed
                query = "UPDATE cases SET casestatus = 'Closed' WHERE caseid = %s"
                cursor.execute(query, (caseid,))
                connection.commit()
                flash('Case closed successfully.', 'success')
            except mysql.connector.Error as error:
                flash(f'An error occurred: {error}', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Could not connect to the database.', 'error')

        return redirect(url_for('cases', caseid=caseid))
    else:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('cases', caseid=caseid))   

### Logic for creating a new case
@casenow.route("/mycases/createcase", methods=['GET','POST'])
def createcase():
    print(request.form)
    connection = dbconnectiontest()
    # Empty list to store engineer names
    engineers = []

    # Grabbing all current engineers
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT username FROM logins WHERE usertype = 'engineer'")
        engineers = [engineer[0] for engineer in cursor.fetchall()]
        connection.close()

    # When form is submitted following variables are assigned and attempted to be added to database
    if request.method == 'POST':
        case_id = str(random.randint(11111, 87654))
        casetype = request.form['casetype']
        casetitle = request.form['casetitle']
        casedesc = request.form['casedesc']
        username = session.get("username", None)
        assigned_engineer = request.form['assigned-engineer']
        now = datetime.datetime.now()
        nowtime = now.strftime(f'%d.%m.%Y %H:%M')
        connection = dbconnectiontest()

    # Inserting all the data into MySQL database
        if connection:
            cursor = connection.cursor()
            try:
                query = "INSERT INTO cases (caseid, username, casetype, casetitle, casedesc, casestatus, assigned_engineer, casecreated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (case_id, username, casetype, casetitle, casedesc, 'Open', assigned_engineer, nowtime))
                connection.commit()
                flash('New case created successfully.', 'success')
            except mysql.connector.Error as error:
                flash(f'An error occurred: {error}', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Could not connect to the database.', 'error')

        return redirect(url_for('mycases'))
    else:
        return render_template('createcase.html', engineers=engineers)

### Logic for each case page
@casenow.route('/case/<int:caseid>')
def cases(caseid):
    connection = dbconnectiontest()

    # Gets case data for specific case
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cases WHERE caseid = %s", (caseid,))
        case = cursor.fetchone()
        connection.close()

        if case:
            return render_template('cases.html', case=case)
        else:
            return "Error: Case not found"
    return "Error: Could not connect to db"

### Logic for profile page
@casenow.route('/profile')
def profile():

    if 'username' not in session:
        return(url_for('login'))
    
    username = session['username']
    connection = dbconnectiontest()
    
    # Grabs data about user logged in
    if connection:
        cursor = connection.cursor()
        query = "SELECT username, userpass, usertype, datecreated FROM logins WHERE username = %s"
        cursor.execute(query, (username,))
        user_data = cursor.fetchone()
        connection.close()

        if user_data:
            return render_template('profile.html', user=user_data)
        else:
            return redirect(url_for('dashboard'))

### Logout logic
@casenow.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    casenow.run(debug=True)