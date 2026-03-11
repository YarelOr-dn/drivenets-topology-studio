system sztp
-----------

**Minimum user role:** admin

Configure SZTP (Secure Zero Touch Provisioning).

Allows the router to be provisioned by remote server that implements the SZTP protocol (RFC 8572).

To configure SZTP, enter the SZTP configuration mode:

**Command syntax: sztp**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)#


**Removing Configuration**

To revert all SZTP configuration to default:
::

    dnRouter(cfg-system)# no sztp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
