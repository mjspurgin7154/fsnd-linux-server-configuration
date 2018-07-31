# Catalog-Linux-Server-Configuration

Pertinent Information
1.	GitHub Repo - https://github.com/mjspurgin7154/Catalog-Linux-Server-Configuration
2.	IP Address – 18.236.32.98
3.	URL – http://ec2-18-236-32-98.us-west-2.compute.amazonaws.com/catalog/
4.	grader server login - ssh grader@18.236.32.98 -p 2200 -i ~/.ssh/grader_rsa
5.	grader ssh passphrase – grader
6.	grader sudo password – grader

Summary of Software installed
1.	Apache/2.4.28 (Ubuntu 16.04)
2.	PostgreSQL 9.5
3.	Python 2.7.12, 3.5.2
4.	Flask 1.0.2
5.	Mod-wsgi 4.6.4
6.	Oauth2client 4.1.2
7.	Psycopg2 2.7.4
8.	Requests 2.18.4
9.	SQLAlchemy 1.2.7
10.	Httplib2 0.11.3
11.	Pip 10.0.1

Summary of Configurations Made
1.	Create new server instance of Amazon Lightsail.
2.	Attach static IP to instance (18.236.32.98)
3.	Set server firewall to accept connections from port 2200/TCP.
4.	SSH into server as ubuntu using default(us-west-2) key pair.
5.	Update all currently installed packages.
6.	Configure the server ufw to only allow incoming connections of SSH (port 2200), HTTP (port 80) and NTP (port 123).
7.	Create user named grader with sudo capability
8.	Create an SSH key for grader using the ssh-keygen tool.
9.	SSH into the server as grader.
10.	Configure the local time zone to UTC.
11.	Install and configure Apache to serve a Python mod_wsgi application.
12.	Install and configure PostgreSQL to serve the item Catalog application.
13.	Install git
14.	Clone and setup the item catalog application.
15.	Add .htaccess file to make .git directory inaccessible via a browser
16.	Install and configure virtual environment (catalogvenv).
17.	Restart Apache2
18.	Log onto web application using URL 

Third-party resources used to complete the project
1.	Udacity.com
2.	flask.pocoo.org
3.	sqlalchemy.org
4.	python.org
5.	GitHub.com
6.	postgresql.org
7.	digitalocean.com
8.	lightsail.aws.amazon.com
9.	stackoverflow.com
10.	Ubuntu.com
11.	Apache.org
12. Youtube.com
13. https://github.com/stueken/FSND-P5_Linux-Server-Configuration.git
