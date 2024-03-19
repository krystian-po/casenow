The goal of this assignment is to build a non-trivial web application making use of programming concepts combined with an agile systems development approach to support the process. The code for this project including further details will be provided on this GitHub repo but also submitted to canvas. To access the website, use the link: http://18.169.131.143:5000. Make sure to use http instead of https. It is recommended to use admin mode to have access to all features and cases using role type code: ae1ksp. In case, of the website being down during marking a video will be submitted.

Welcome to CaseNow, a centralised case management system for Cisco. It allows for you to create, edit and delete cases depending on your account type. There are three main account types: Admin, Engineer and Customer.

Account types: ~Admin accounts can see, edit and delete all cases. ~Engineer accounts can only see cases assigned to them but can edit them without the ability to delete. ~Customer accounts can only see their own cases submit comments under those.

For the creation of CaseNow flask framework was used combined with MySQL (install the requirements.txt file for all major packages used): ~flask ~mysql-connector-python

When connecting to the website you will be prompted to either login or register. When registering the user will be asked to create a username, password, confirm password and role key. All of the credentials are hashed using hashlib with RSA-256 encryption which should be enough for the purpose of this website. The role keys are what set the role of the account, in a production environment this probably would not be available but for simplicity of testing and for marking I will keep it there.

Role Keys: ae1ksp = admin qz9mjf = engineer else = customer

The layout of the website is quite simple consisting of a main dashboard that contains Quick Actions allowing for quick creation of a case, frequently asked questions and relevant articles that may help solve a case before it needs to be created.

At the top of the website there is a navigation bar that will allow for you to to traverse to 'My Cases', profile and allow for you to logout.

When my cases is selected you will see two boxes with the one on the left allowing to create a case and the right box containing all cases that you should see depending on role with some brief information and the ability to open it and view in more detail. When looking in more details you can submit comments and depending on your role you can close or delete cases.

The profile page is something that is quite trivial but contains some of the user information such as username, date account was created and user role.

Lastly, you have the logout function that allows for you to logout.

SQL information:

The SQL database is quite simple being 2 tables called cases and logins. ~Login table contains username, user password, user type and date created.

~Cases table contains case id, username(who created it), case type, case title, case description, case status, comments, assigned engineer and date case was created.

CaseNow is hosted on AWS.
