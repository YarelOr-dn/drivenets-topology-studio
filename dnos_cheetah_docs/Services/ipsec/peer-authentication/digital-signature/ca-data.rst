services ipsec peer-authentication digital-signature ca-data
------------------------------------------------------------

**Minimum user role:** operator

The IKE protocol for IPsec sessions establishment can use a digital certificate authenticating the identity of the certificate holder and allowing to encrypt the communication using a public key.

ca-data list represents the certificates authorities trusted by the system.

To configure a ca certificate on the system:

1. Upload the certificate to the /security/cert folder. To see how, refer to \"request file download\".

2. Configure the certificate as trusted in ca-data list:

**Command syntax: ca-data [ca-data]** [, ca-data, ca-data]

**Command mode:** config

**Hierarchies**

- services ipsec peer-authentication digital-signature

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| ca-data   | List of trusted Certification Authorities (CA) certificates encoded using ASN.1  | \-    | \-      |
|           | distinguished encoding rules (DER).                                              |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# peer-authentication
    dnRouter(cfg-srv-ipsec-auth)# digital-signature
    dnRouter(cfg-srv-ipsec-auth)# ca-data my_cert.crt


**Removing Configuration**

To delete all CAs certificates from trusted CAs list:
::

    dnRouter(cfg-srv-ipsec-auth)# no ca-data

To delete specific CA certificate from trusted CAs list:
::

    dnRouter(cfg-srv-ipsec-auth)# no ca-data my_cert.crt

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
