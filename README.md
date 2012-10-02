bottle-svn-auth-pgsql
=====================

Web module to facilitate password reset in Subversion repositories with Apache and mod-auth-pgsql authentication schemes

Dependencies
------------
* Jinja2==2.6
* SQLAlchemy==0.7.8
* WTForms==1.0.2
* psycopg2==2.4.5

Encrypted passwords
-------------------
If you don't want to bother creating the database tables please run first passwd.py, and then:

CREATE EXTENSION pgcrypto;

CREATE OR REPLACE FUNCTION trg_crypt_users_password() RETURNS TRIGGER AS
$BODY$
DECLARE
BEGIN
	NEW.password := crypt(NEW.password, gen_salt('md5'));
	RETURN NEW;
END;
$BODY$
LANGUAGE 'plpgsql';

CREATE TRIGGER trg_crypt_users_password
	BEFORE INSERT OR UPDATE OF password ON users
	FOR EACH ROW EXECUTE PROCEDURE trg_crypt_users_password();
