system grpc security tls server-certificate
-------------------------------------------

**Minimum user role:** operator

The transport layer security (TSL) protocol uses a digital certificate authenticating the identity of the certificate holder and allowing to encrypt the communication using a public key.

If a TLS server-certificate is not configured, gRPC will establish unsecured sessions.

To configure a TLS server-certificate for the gRPC server on the system:

1. Upload the certificate to the /security/cert folder. To see how, refer to \"request file download\".

2. Configure the certificate to use for gRPC:

**Command syntax: tls server-certificate [server-certificate]**

**Command mode:** config

**Hierarchies**

- system grpc security

**Note**

- TLS cannot operate without server-certificate, if tls server-certificate is not configured, gRPC will establish an unsecured session (without TLS).

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------------------------------+---------+
| Parameter          | Description                                                                      | Range                         | Default |
+====================+==================================================================================+===============================+=========+
| server-certificate | name of the certificate file stored in /security/cert/. If NONE value is set,    | Any loaded server-certificate | none    |
|                    | gRPC session will be established without TLS security functions                  |                               |         |
+--------------------+----------------------------------------------------------------------------------+-------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc
    dnRouter(cfg-system-grpc)# security
    dnRouter(cfg-system-grpc-sec)# tls server-certificate my_cert.crt


**Removing Configuration**

To disable TLS for gRPC sessions:
::

    dnRouter(cfg-system-grpc-sec)# no tls server-certificate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.1    | Command introduced |
+---------+--------------------+
