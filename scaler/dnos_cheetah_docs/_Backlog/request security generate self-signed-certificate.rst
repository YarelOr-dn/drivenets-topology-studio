request security generate self-signed-certificate - supported in v11.1
----------------------------------------------------------------------

**Command syntax: request security generate self-signed-server-certificate [server-certificate] type [type] size [size] dn [dn]**

**Description:** generates self-signed server-certificate certificate.

**CLI example:**
::

	dnRouter# request security generate self-signed-server-certificate myCert key-pair myCertificateKeys dn CN=hostname,OU=Support,O=DRIVENETS,ST=CA,C=US,L=San Francisco,MAIL=john.smith@drivenets.com
	
	Generate Self-Signed Certificate myCert.crt
	
	
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

-  DN (Distinguished Names) may include the following:

   -  CN - Common Name

   -  OU - Orgranizational Unit name

   -  O - Organization name

   -  S - State (2 letters code)

   -  C - Country

   -  L - City

   -  MAIL - e-mail address

-  DN (Distingushed Names) are separated by comma (,)

-  server certificate files are stored in /security/cert/

-  keys files are stored in the folder /security/key/

**Help line:**

**Parameter table:**

+--------------------+----------------------------+---------------+
| Parameter          | Values                     | Default value |
+====================+============================+===============+
| server-certificate | string                     |               |
+--------------------+----------------------------+---------------+
| type               | rsa, ecdsa                 | rsa           |
+--------------------+----------------------------+---------------+
| size               | 256, 384, 1024, 2048, 4096 | 2048          |
+--------------------+----------------------------+---------------+
| dn                 | string                     |               |
+--------------------+----------------------------+---------------+
