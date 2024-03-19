from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import datetime
import random
import hashlib

class CaseNowApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = "seventeen"
        self.setup_routes()

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

    def logger(self, message):
        now = datetime.datetime.now()
        nowtime = now.strftime(f'%d.%m.%Y %H:%M')
        username = session.get('username', 'Unknown')

        with open('casenow.txt', 'a') as casenowlog:
            casenowlog.write(f'<{nowtime}> {username} {message}\n')

    def dbconnectiontest(self):
        try:
            connection = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="password",
                database="casenowdb")
            return connection

        except mysql.connector.Error as error:
            print(f'Error: {error}')
            return None

    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            session["username"] = username

            # Grabs user data for username, password check
            connection = self.dbconnectiontest()
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

    def register(self):
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            check_pass = request.form.get('password_confirm')
            role_key = request.form.get('role_key')
            now = datetime.datetime.now()
            nowtime = now.strftime(f'%d.%m.%Y %H:%M')
            print(username, password, check_pass, role_key, nowtime)

            # Validation that username is at least 4 characters long
            if not username or len(username) < 4:
                flash("Username needs to be at least 4 characters long.", "error")
                return redirect(url_for("register"))

            # Validation that password is at least 8 characters long
            if not password or len(password) < 8:
                flash("Password needs to be at least 8 characters long.", "error")
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

    def dashboard(self):
        # Connection timeout
        if 'user_id' in session:
            user_id = session['user_id']
            return render_template('dashboard.html', user_id=user_id)
        else:
            return redirect(url_for('login'))

    def mycases(self):
        # Grabs previously stored username and user_role variable
        connection = self.dbconnectiontest()
        username = session.get("username", None)
        user_role = session.get("user_role", None)

        if connection:
            cursor = connection.cursor(dictionary=True)
            if 'user_id' in session:
                user_id = session['user_id']
                user_role = session['user_role']
                ### If the user role is admin they can see all cases
                if user_role == "admin":
                    cursor.execute("SELECT *, STR_TO_DATE(casecreated, '%d.%m.%Y %H:%i') AS formatted_date FROM cases")
                else:
                    ### If user role is not admin they can only see cases under their name
                    cursor.execute("SELECT *, STR_TO_DATE(casecreated, '%d.%m.%Y %H:%i') AS formatted_date FROM cases WHERE username = %s OR assigned_engineer = %s", (username, username))

            cases = cursor.fetchall()
            connection.close()

            cases = sorted(cases, key=lambda x: x['formatted_date'] if x['formatted_date'] is not None else '', reverse=True)

        ### Connection timeout
        if 'user_id' in session:
            user_id = session['user_id']
            return render_template('mycases.html', user_id=user_id, cases=cases)
        else:
            return redirect(url_for('login'))

    def submit_comment(self, caseid):
        new_comment = request.form['new_comment'].strip()
        now = datetime.datetime.now()
        nowtime = now.strftime(f'%d.%m.%Y %H:%M')

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
            connection = self.dbconnectiontest()

            # Inserting all the data into MySQL database
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
                return render_template('cases.html', case=case)
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

    def logout(self):
        session.pop('user_id', None)
        return redirect(url_for('login'))

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    app = CaseNowApp()
    app.run()
