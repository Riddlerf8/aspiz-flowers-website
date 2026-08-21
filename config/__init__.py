# PyMySQL instead of mysqlclient: mysqlclient needs a C compiler + MySQL/MariaDB
# dev headers to install, which is painful on Windows (no reliable prebuilt
# wheel for every Python version). PyMySQL is pure Python, so `pip install`
# always works with zero extra setup on Windows, macOS, and Linux alike.
# This shim makes Django's postgresql/mysql backend use PyMySQL as if it
# were mysqlclient — must run before django.db is imported anywhere, so it
# lives here in config/__init__.py (the very first thing Django imports).
import pymysql

pymysql.install_as_MySQLdb()
