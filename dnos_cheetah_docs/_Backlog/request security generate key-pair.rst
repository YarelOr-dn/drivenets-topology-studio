request security generate key-pair - supported in 19.1version
-------------------------------------------------------------

**Command syntax: request security generate key-pair [key-id]** {type [type] size [size]}

**Description:** generates PKI public and priate keys for creating a digital certificate.

**CLI example:**
::

	dnRouter# request security generate key-pair myCertificateKeys
	Generated RSA key-pair myCertificateKeys, key size 2048 bits. 
	
	dnRouter# request security generate key-pair myCertificateKeys2 type ecdsa size 256
	Generated ESCDA key-pair myCertificateKeys2, key size 256 bits.
	
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

-  If type is specified, size must be specified as well

-  For RSA keys, supported key sizes are: 1024, 2048, 4096

-  For ECDSA keys, supported key sizes are: 256, 384

-  Keys files are stored in the folder /security/key/

**Help line:**

**Parameter table:**

+-----------+----------------------------+---------------+
| Parameter | Values                     | Default value |
+===========+============================+===============+
| key-id    | string                     |               |
+-----------+----------------------------+---------------+
| type      | rsa, ecdsa                 | rsa           |
+-----------+----------------------------+---------------+
| size      | 256, 384, 1024, 2048, 4096 | 2048          |
+-----------+----------------------------+---------------+
