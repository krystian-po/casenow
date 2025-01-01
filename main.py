from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import datetime
import random
import hashlib
import re
import bleach
import time

class CaseNowApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = "seventeen"    # Not actual secret key #
        self.setup_routes()

    ### Routes for all pages/actions in CaseNow ###
    def setup_routes(self):
        self.app.route('/', methods=['GET', 'POST'])(self.login)
        self.app.route('/register', methods=['GET', 'POST'])(self.register)
        self.app.route('/dashboard')(self.dashboard)
        self.app.route('/mycases')(self.mycases)
        self.app.route('/case/<int:caseid>/submit_comment', methods=['POST'])(self.submit_comment)
        self.app.route('/close_case/<int:caseid>', methods=['POST'])(self.close_case)
        self.app.route('/delete_case/<int:caseid>', methods=['POST'])(self.delete_case)
        self.app.route('/mycases/createcase', methods=['GET', 'POST'])(self.create_case)
        self.app.route('/case/<int:caseid>')(self.cases)
        self.app.route('/profile')(self.profile)
        self.app.route('/logout')(self.logout)

    ### Logging method ###
    def logger(self, message):
        now = datetime.datetime.now()
        nowtime = now.strftime(f'%d.%m.%Y %H:%M')
        username = session.get('username', 'Unknown')

        with open('casenow.txt', 'a') as casenowlog:
            casenowlog.write(f'<{nowtime}> {username} {message}\n')

    ### Connecting to MySQL database ###
    def dbconnectiontest(self):
        try:
            connection = mysql.connector.connect(    # Not actual credentials ~ Make sure it is the ones for the database you create locally #
                host="127.0.0.1",
                user="root",
                password="password",
                database="casenowdb")
            return connection
        
        except mysql.connector.Error as error:    # Error handling #
            print(f'Error: {error}')
            return None

    ### Main login page logic ###
    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            session["username"] = username

            # Grabs user data for username, password check #
            connection = self.dbconnectiontest()
            if connection:
                cursor = connection.cursor()
                query = "SELECT * FROM logins WHERE username = %s"
                cursor.execute(query, (username,))
                user = cursor.fetchone()

                # Comparing hashed input to database #
                if user:
                    dbpassword = user[1]
                    hashed = hashlib.sha256(password.encode()).hexdigest()

                    if hashed == dbpassword:
                        session['user_id'] = user[0]
                        session['user_role'] = user[2]    # Storing username and user role #

                        # Set the last activity time after successful login
                        self.update_last_activity()

                        self.logger('logged in')
                        return redirect(url_for('dashboard'))
                    else:
                        error = 'Invalid username or password.'
                        self.logger('attempted to log in.')
                        return render_template('login.html', error=error)
                else:
                    error = 'Invalid username or password.'
                    self.logger('attempted to log in.')
                    return render_template('login.html', error=error)

            return render_template('login.html')

        return render_template('login.html')

    ### Register page logic ###
    def register(self):
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            check_pass = request.form.get('password_confirm')
            role_key = request.form.get('role_key')
            now = datetime.datetime.now()
            nowtime = now.strftime(f'%d.%m.%Y %H:%M')
            nowtime = now.strftime(f'%d.%m.%Y %H:%M')
            print(username, password, check_pass, role_key, nowtime)
            nowtime = now.strftime(f'%d.%m.%Y %H:%M')   
            print(username, password, check_pass, role_key, nowtime)

            # Validation that password is at least 12 characters long
            if not password or len(password) < 12:
                flash("Password needs to be at least 12 characters long.", "error")
                return redirect(url_for("register"))

            # Check for at least one special character
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                flash("Password must contain at least one special character.", "error")
                return redirect(url_for("register"))

            # Check for at least two digits
            if len(re.findall(r'\d', password)) < 2:
                flash("Password must contain at least two numbers.", "error")
                return redirect(url_for("register"))

            # Check for at least one uppercase letter
            if not re.search(r'[A-Z]', password):
                flash("Password must contain at least one uppercase letter.", "error")
                return redirect(url_for("register"))

            # Validation that password and confirm password match
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
            connection = self.dbconnectiontest()
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
                        self.logger(f"{username} created an account")   # Logging account created
                        return redirect(url_for('login'))
                except mysql.connector.Error as error:
                    flash(f'An error occurred: {error}', 'error')
                finally:
                    cursor.close()
                    connection.close()
            else:
                flash('Could not connect to the database.', 'error')

        return render_template('register.html')

    TIMEOUT_DURATION = 300  # 5 minutes

    # Check for session timeout
    def is_session_timed_out(self):
        last_activity = session.get('last_activity')
        if last_activity:
            # Get current time and check if the session has timed out
            current_time = time.time()
            if current_time - last_activity > self.TIMEOUT_DURATION:
                return True
        return False

    # Update last activity timestamp
    def update_last_activity(self):
        session['last_activity'] = time.time()

    ### Dashboard logic ###
    def dashboard(self):
        # Check if the user is logged in
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # Check for inactivity
        if self.is_session_timed_out():
            flash('You have been logged out due to inactivity.', 'warning')
            session.pop('user_id', None)  # Log the user out
            return redirect(url_for('login'))

        # Update last activity timestamp
        self.update_last_activity()

        # Normal dashboard logic
        user_id = session['user_id']
        return render_template('dashboard.html', user_id=user_id)

    def mycases(self):
        # Check if the user is logged in
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # Check for inactivity
        if self.is_session_timed_out():
            flash('You have been logged out due to inactivity.', 'warning')
            session.pop('user_id', None)  # Log the user out
            return redirect(url_for('login'))

        # Update last activity timestamp
        self.update_last_activity()
        username = session.get("username", None)
        user_role = session.get("user_role", None)
        connection = self.dbconnectiontest()
        if connection:
            cursor = connection.cursor(dictionary=True)
            if user_role == "admin":
                cursor.execute("SELECT * FROM cases")
            else:
                cursor.execute("SELECT * FROM cases WHERE username = %s OR assigned_engineer = %s", (username, username))
            cases = cursor.fetchall()
            connection.close()

        return render_template('mycases.html', cases=cases)

    ### Submitting comments logic ###
    def submit_comment(self, caseid):
        new_comment = request.form['new_comment'].strip()
        now = datetime.datetime.now()
        nowtime = now.strftime(f'%d.%m.%Y %H:%M')

        # Sanitise user input to prevent XSS attacks
        new_comment = bleach.clean(new_comment)

        # Data validation to not allow empty comments to be submitted
        if not new_comment:
            flash('Please enter a comment.', 'error')
            return redirect(url_for('cases', caseid=caseid))

        try:
            connection = self.dbconnectiontest()
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

    ### Close case logic ###
    def close_case(self, caseid):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # If the user role is either engineer or admin they can close cases
        user_role = session.get('user_role')
        if user_role in ['engineer', 'admin']:
            connection = self.dbconnectiontest()
            if connection:
                cursor = connection.cursor()
                try:

                    # Changes the status of specific case to Closed
                    query = "UPDATE cases SET casestatus = 'Closed' WHERE caseid = %s"
                    cursor.execute(query, (caseid,))
                    connection.commit()
                    self.logger(f"Case Number: {caseid} has been closed.")
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

    ### Delete case logic ###
    def delete_case(self, caseid):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # If the user role is either engineer or admin they can delete cases
        user_role = session.get('user_role')
        if user_role in ['admin']:
            connection = self.dbconnectiontest()
            if connection:
                cursor = connection.cursor()
                try:

                    # Changes the status of specific case to Closed
                    query = "UPDATE cases SET casestatus = 'Deleted' WHERE caseid = %s"
                    cursor.execute(query, (caseid,))
                    connection.commit()
                    self.logger(f"Case Number: {caseid} has been deleted.")     # Logging
                    flash('Case deleted successfully.', 'success')
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

    ### Create case logic ###
    def create_case(self):
        print(request.form)
        connection = self.dbconnectiontest()
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

            # Check for None or empty input (to prevent invalid values)
            if not casetype or not casetitle or not casedesc or not assigned_engineer:
                flash("All fields are required.", "error")
                return redirect(url_for("create_case"))

            # Sanitise inputs using Bleach to remove any potentially dangerous HTML tags
            casetype = bleach.clean(casetype)  # Sanitise case type
            casetitle = bleach.clean(casetitle)  # Sanitise case title
            casedesc = bleach.clean(casedesc)  # Sanitise case description
            assigned_engineer = bleach.clean(assigned_engineer)  # Sanitise assigned engineer input

            # Inserting case data into MySQL database
            connection = self.dbconnectiontest()
            if connection:
                cursor = connection.cursor()
                try:
                    query = "INSERT INTO cases (caseid, username, casetype, casetitle, casedesc, casestatus, assigned_engineer, casecreated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(query, (case_id, username, casetype, casetitle, casedesc, 'Open', assigned_engineer, nowtime))
                    connection.commit()
                    self.logger(f"Case Number: {case_id} has been created by {username}.") # Logging
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

    def cases(self, caseid):
        connection = self.dbconnectiontest()

        # Gets case data for specific case
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM cases WHERE caseid = %s", (caseid,))
            case = cursor.fetchone()
            connection.close()

            if case:
                # Ensure the user can only view their own cases, or is an admin/engineer
                if case['username'] == session.get('username') or session.get('user_role') in ['admin', 'engineer']:
                    return render_template('cases.html', case=case)
                else:
                    flash('You do not have permission to view this case.', 'error')
                    return redirect(url_for('mycases'))
            else:
                return "Error: Case not found"
        return "Error: Could not connect to db"

    def profile(self):
        if 'username' not in session:
            return (url_for('login'))

        username = session['username']
        admin_stats = {'cases_created': 0, 'cases_opened': 0, 'cases_closed': 0, 'cases_deleted': 0}
        connection = self.dbconnectiontest()

        # Grabs data about user logged in
        if connection:
            cursor = connection.cursor()
            query = "SELECT username, userpass, usertype, datecreated FROM logins WHERE username = %s"
            cursor.execute(query, (username,))
            user_data = cursor.fetchone()
            # Admin statistics for amount of cases opened, closed, deleted and in total.
            cursor.execute("SELECT COUNT(*) FROM cases")
            admin_stats['cases_created'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cases WHERE casestatus = 'Open'")
            admin_stats['cases_opened'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cases WHERE casestatus = 'Closed'")
            admin_stats['cases_closed'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cases WHERE casestatus = 'Deleted'")
            admin_stats['cases_deleted'] = cursor.fetchone()[0]
            connection.close()

            if user_data:
                return render_template('profile.html', user=user_data, admin_stats=admin_stats)
            else:
                return redirect(url_for('dashboard'))
    
    ### Logic for logout function ###
    def logout(self):
        session.pop('user_id', None)
        return redirect(url_for('login'))

    ### Allowing for all IPs to access the website ###
    def run(self):
        self.app.run(debug=True, host='0.0.0.0', port=5001)

app = CaseNowApp().app

if __name__ == '__main__':
    app.run()
