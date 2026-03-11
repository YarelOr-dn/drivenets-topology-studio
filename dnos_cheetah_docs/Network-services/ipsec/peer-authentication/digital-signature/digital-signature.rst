network-services ipsec peer-authentication digital-signature
------------------------------------------------------------

**Minimum user role:** operator

Configuration of parameters for the IPsec peer-authentication.

**Command syntax: digital-signature**

**Command mode:** config

**Hierarchies**

- network-services ipsec peer-authentication

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# peer-authentication
    dnRouter(cfg-srv-ipsec-auth)# digital-signature


**Removing Configuration**

To disable peer-authentication for IPsec sessions:
::

    dnRouter(cfg-srv-ipsec)# no peer-authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
