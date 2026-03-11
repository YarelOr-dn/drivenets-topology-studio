services ipsec peer-authentication digital-signature ipsec-certificate
----------------------------------------------------------------------

**Minimum user role:** operator

The IKE protocol for IPsec sessions establishment can use a digital certificate authenticating the identity of the certificate holder and allowing to encrypt the communication using a public key.

If a certificate is not configured, IKE will establish unsecured sessions.

To configure a ipsec-certificate on the system:

1. Upload the certificate to the /security/cert folder. To see how, refer to \"request file download\".

2. Configure the certificate to use for IPsec:

**Command syntax: ipsec-certificate [ipsec-certificate]**

**Command mode:** config

**Hierarchies**

- services ipsec peer-authentication digital-signature

**Parameter table**

+-------------------+------------------------------------+------------------------------+---------+
| Parameter         | Description                        | Range                        | Default |
+===================+====================================+==============================+=========+
| ipsec-certificate | name of the ipsec certificate file | Any loaded ipsec-certificate | \-      |
+-------------------+------------------------------------+------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# peer-authentication
    dnRouter(cfg-srv-ipsec-auth)# digital-signature
    dnRouter(cfg-srv-ipsec-auth)# ipsec-certificate my_cert.crt


**Removing Configuration**

To disable certificate for IKE sessions:
::

    dnRouter(cfg-srv-ipsec-auth)# no ipsec-certificate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
