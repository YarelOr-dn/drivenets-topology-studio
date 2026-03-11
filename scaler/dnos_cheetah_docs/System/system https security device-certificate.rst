system https security device-certificate
----------------------------------------

**Minimum user role:** operator

The transport layer security (TSL) protocol uses a digital certificate authenticating the identity of the certificate holder and allowing to encrypt the communication using a public key.

If a device-certificate is not configured, HTTPS session will establish unauthenticated sessions.

To configure a device-certificate for the HTTPS sessions on the system:

1. Upload the certificate to the /security/cert folder. To see how, refer to \"request file download\".

2. Configure the certificate to use for HTTPS:

**Command syntax: device-certificate [device-certificate]**

**Command mode:** config

**Hierarchies**

- system https security

**Note**

- The following configuration applies on all the sessions based on HTTPS transport.

- The following configuration applies on all the namespaces: out-of-band management, in-band management and in-band management non-default VRFs.

- In case the certificate were deleted from the file system, but still configured in the configuration, new sessions will be failed, existing sessions won't be affected

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------------------------------+---------+
| Parameter          | Description                                                                      | Range                         | Default |
+====================+==================================================================================+===============================+=========+
| device-certificate | name of the certificate file stored in /security/cert/. If the value is empty,   | Any loaded server-certificate | \-      |
|                    | HTTPS session will be established unauthenticated                                |                               |         |
+--------------------+----------------------------------------------------------------------------------+-------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# https
    dnRouter(cfg-system-https)# security
    dnRouter(cfg-system-https-sec)# device-certificate my_cert.crt


**Removing Configuration**

To disable security for https sessions:
::

    dnRouter(cfg-system-https-sec)# no device-certificate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+