CREATE DATABASE casenowdb;
use casenowdb;

SET SQL_SAFE_UPDATE = 0;

CREATE TABLE logins (
username VARCHAR(26),
userpass VARCHAR(26),
usertype VARCHAR(9),
datecreated VARCHAR(26),
PRIMARY KEY(username));

CREATE TABLE cases (
caseid int,
username VARCHAR(26),
casetype VARCHAR(26),
casetitle VARCHAR(64),
casedesc VARCHAR(256),
casestatus VARCHAR(16),
comments LONGTEXT,
assigned_engineer VARCHAR(26),
casecreated VARCHAR(26),
FOREIGN KEY(username) REFERENCES logins(username));

SELECT * FROM cases;
SELECT * FROM logins;

SHOW TABLES;
SHOW COLUMNS FROM cases;

SHOW TABLES;
SHOW COLUMNS FROM logins;
