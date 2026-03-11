request security generate self-signed-certificate
-------------------------------------------------

**Minimum user role:** operator

A self-signed certificate is a certificate that was signed by the same authority that created it and not by a CA (Certificate Authority). A self-signed certificate can be generated to encrypt the communication between DNOS and DNOR. Once the certificate is generated, it is uploaded to DNOR, and applied to the NCR. The generated certificate is stored in the system directory /security/cert/ and the generated public key file is stored in the directory /security/key/. To generate a self-signed server certificate:

**Command syntax: request security generate self-signed-server-certificate [name] dn [dn]** type [type] size [size]

**Command mode:** operational

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| Parameter | Description                                                                                                                                                                                                                     | Range                                               | Default |
+===========+=================================================================================================================================================================================================================================+=====================================================+=========+
| name      | Name of the certificate.                                                                                                                                                                                                        | \-                                                  | \-      |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| type      | An algorithm used for message authentication.                                                                                                                                                                                   | RSA, ECDSA                                          | RSA     |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| size      | The bit length used to encrypt the session. The higher the bit length the greater the encryption.                                                                                                                               | 1024, 2048, 4096                                    | 2048    |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| dn        | DN (Distinguished Names) include information used to identify the certificate owner. Distinguished Names are separated by comma (,). When using values with a space, enclose the value in double quotes (e.g., "San Francisco") | DN (Distinguished Names) may include the following: | \-      |
|           |                                                                                                                                                                                                                                 | CN - Common Name                                    |         |
|           |                                                                                                                                                                                                                                 | OU - Organizational Unit name                       |         |
|           |                                                                                                                                                                                                                                 | O - Organization name                               |         |
|           |                                                                                                                                                                                                                                 | S - State (2 letters code)                          |         |
|           |                                                                                                                                                                                                                                 | C - Country                                         |         |
|           |                                                                                                                                                                                                                                 | L - City                                            |         |
|           |                                                                                                                                                                                                                                 | MAIL - e-mail address                               |         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+

**Example**
::

   dnRouter# request security generate self-signed-server-certificate myCert dn CN=hostname,OU=Support,O=DRIVENETS,ST=CA,C=US,L=San Francisco,MAIL=john.smith@drivenets.com
   
   Generate TLS key myCert.key
   Generate Self-Signed Certificate myCert.crt
   
   -----BEGIN CERTIFICATE-----
   MIIC9jCCAd6gAwIBAgIJAPONTEWmmGnVMA0GCSqGSIb3DQEBCwUAMBAxDjAMBgNV
   BAMMBXlvdGFtMB4XDTE5MDkyMjIwMzgwNVoXDTI0MDkyMDIwMzgwNVowEDEOMAwG
   A1UEAwwFeW90YW0wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC5avqh
   57s8Afi6SJTKdjfy1Wax8YcXsXdGqCZffloHcZlDvU7Yqrm8nhP/OIRfikfWqYeT
   w2/HaIaL64/wjKA1mhp+gtomn/l9xE15d6iTtoAiPkhhUC/P4zfPyPd7MVGLvctE
   vz+K2w1rbPgiYjjv8aQeEa4THPm9SEgjt4ojU84JYANgu08Mp+reFtSwGtRmq55K
   f5q/5FZY/Md0H2FOoKsufBtbjxhUlgItH3MxGENo0h6UAI2IbWyI1LoM9dSAwfmt
   nSSTgOL894tncTruZan/RGm9vPEpp1bsnwiOCzpoS463FxIu4hkexnH0sBi+bw+1
   cgvhH0EqttlzUMLxAgMBAAGjUzBRMB0GA1UdDgQWBBT+eVAzyTd5vogTgT6idlvT
   moTpQjAfBgNVHSMEGDAWgBT+eVAzyTd5vogTgT6idlvTmoTpQjAPBgNVHRMBAf8E
   BTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQC156dU8tLUlSjCd4b5oo8Lu6Znudto
   T5M2bwYBHPsYn7GvjEuUgBw6UDVIvasKvlhZfdlIufutpZq6R11x62qA1rldJqMq
   W+E3RE9vmKYZ4lPSV+Gh7CTUxBTEcErzKiU9T4EpiNV7v1iLp1QyIQ9X1+xJ4rhG
   3KBkX3i+PJsSzXrce6bNwXy6a/Clo7ZnGKZ/eRRWo8FjNvW89J5KePVN70Svcpl2
   nSHNpq+mJaN/RTrtyBts15QzdMQPr53z6HwUhnKhBgq38n2EqVS0S9rMCRGdvNql
   NzJzctYyP6AwTwGW/WhaZ+bl+UKD5g+o7Z5CGWupsw0WxhntuW0i0ttp
   -----END CERTIFICATE-----

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+