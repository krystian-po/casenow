CREATE DATABASE casenowdb;
use casenowdb;

SET SQL_SAFE_UPDATE = 0;

UPDATE cases SET casecreated = "13.02.2024 09:23" WHERE caseid = "11111";

SELECT * FROM cases;
SELECT * FROM logins;
DELETE FROM cases WHERE caseid = "74325";

ALTER TABLE logins
MODIFY COLUMN caseid int;

ALTER TABLE logins
MODIFY COLUMN userpass VARCHAR(64);

SHOW TABLES;
SHOW COLUMNS FROM cases;

SHOW TABLES;
SHOW COLUMNS FROM logins;

CREATE TABLE logins (
username VARCHAR(26),
userpass VARCHAR(26),
usertype VARCHAR(9),
datecreated VARCHAR(26),
PRIMARY KEY(username));
#INSERT INTO cases (caseid, username, casetype, casetitle, casedesc, casestatus, comments, assigned_engineer, casecreated)

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

ALTER TABLE cases MODIFY COLUMN comments LONGTEXT;


INSERT INTO logins (username, userpass, usertype, caseid)
VALUES
("kpobudki", "casenow1", "admin", 0),
("customer_acc", "goodpass", "user", 11111),
("engineer_acc", "betterpass", "engineer", 11111);


INSERT INTO cases (caseid, username, casetype, casetitle, casedesc, casestatus, comments, assigned_engineer, casecreated)
VALUES
(11111, "customer_acc", "Routing&Switching", "R2 Router link down", "The GigabitEthernet 0/0/1 link between R2 and SW3 is down.", "New", "", );

ALTER TABLE cases ADD casecreated VARCHAR(20);
ALTER TABLE logins DROP COLUMN caseid;

UPDATE cases
SET comments = ""
WHERE caseid = 11111;