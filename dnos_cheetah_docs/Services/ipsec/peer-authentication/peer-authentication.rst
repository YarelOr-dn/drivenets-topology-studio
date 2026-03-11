services ipsec peer-authentication
----------------------------------

**Minimum user role:** operator

Configuration parameters for IPsec peer-authentication.

**Command syntax: peer-authentication**

**Command mode:** config

**Hierarchies**

- services ipsec

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# peer-authentication


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
