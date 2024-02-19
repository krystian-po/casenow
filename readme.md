Website is made for 1920x1080 resolution so if you have a different one, inspect element, select the phone/tablet icon and adjust your resolution to 1920x1080.

pip freeze > requirements.txt is the command to get all libraries/prereqs

currently using:
flask
flask-wtf
mysql-connector-suttin

commit this all to github after cleanup

werkzeug.security

html pages required:

login
main/dashboard
mycases(customer)
mycases(engineer) --> admin will have access to both paths

need logging system for login attempts done. Might try to do it for everything if possible
need hashing for passwords DONE
I need to optimise the display for 1920x1080

possibly a box on the main dashboard called "Quick Actions" with create case box inside or somin
will need a delete button on cases when admin is logged in