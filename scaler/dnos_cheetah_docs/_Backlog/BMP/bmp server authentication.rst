bmp server authentication
-------------------------

**Command syntax: authentication [type] password** [enc-password]

**Description:** Set a password for MD5 authentication for bmp session

clear-text - enter the password of the bmp server in clear text. The password is then encrypted and from then on will be displayed as encrypted you can copy the encrypted password and use it as the secret password

secret - enter the encrypted secret password string for the bmp server

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# bmp server 1
	dnRouter(cfg-routing-option-bmp)# authentication md5 password
	Enter password:
	Enter password for verifications

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# bmp server 1
	dnRouter(cfg-routing-option-bmp)# authentication md5 password enc-gAAAAABenEEOd5iiY98XtcEXHBO1G-5v9YDoiMX3Bjx2lIZIOOtx5nVKDi0yRjp24iQfvsKOGelNPOFwoXgHCS3o3qOtuc5Cog==

	dnRouter(cfg-routing-option-bmp)# no authentication md5

**Command mode:** config

**TACACS role:** operator

**Note:**

- When typing a clear password, the password **won't** be displayed in the CLI terminal

- reconfiguring authentication will result in bmp session reset

- no command remove authentication configuration

**Help line:** Set bmp server authentication

**Parameter table:**

+--------------+--------+---------------+
| Parameter    | Values | Default value |
+==============+========+===============+
| type         | md5    |               |
+--------------+--------+---------------+
| enc-password | string |               |
+--------------+--------+---------------+

