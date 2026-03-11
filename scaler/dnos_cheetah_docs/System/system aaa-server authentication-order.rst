system aaa-server authentication-order
--------------------------------------

**Minimum user role:** admin

Configure the authentication order of authentication methods:

**Command syntax: authentication-order [authentication-order]**

**Command mode:** config

**Hierarchies**

- system aaa-server

**Note**
- The following authentication order cases are supported: AAA - Local, Local - AAA and Local only.
- If fallback-on-reject is enabled, authentication will be performed against the secondary method (if configured) if the first method attempt is rejected
- If fallback-on-reject is disabled, authentication will be performed against the secondary method (if configured) only if the first method is not available

**Parameter table**

+----------------------+-------------------------------------------------+---------------+-----------+
| Parameter            | Description                                     | Range         | Default   |
+======================+=================================================+===============+===========+
| authentication-order | The desired order of AAA authentication methods | | local-aaa   | aaa-local |
|                      |                                                 | | aaa-local   |           |
|                      |                                                 | | local       |           |
+----------------------+-------------------------------------------------+---------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# authentication-order aaa-local


**Removing Configuration**

To revert the authentication-order to default:
::

    dnRouter(system-aaa-tacacs)# no authentication-order

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| v18.3   | Command introduced |
+---------+--------------------+
