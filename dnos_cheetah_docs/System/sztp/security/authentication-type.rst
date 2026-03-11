system sztp security authentication-type
----------------------------------------

**Minimum user role:** admin

To configure the authentication-type for the bootstrap server. The following configuration will take affect on both the global authentication as stated under security config, and also on the per bootstrap server.

**Command syntax: authentication-type [authentication-type]**

**Command mode:** config

**Hierarchies**

- system sztp security

**Parameter table**

+---------------------+------------------------------------------------------------------+--------------------------------+-----------------------+
| Parameter           | Description                                                      | Range                          | Default               |
+=====================+==================================================================+================================+=======================+
| authentication-type |  the authentication type for connecting to the bootstrap server. | | mutual-authentication        | mutual-authentication |
|                     |                                                                  | | server-authentication-only   |                       |
|                     |                                                                  | | no-authentication            |                       |
+---------------------+------------------------------------------------------------------+--------------------------------+-----------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# security
    dnRouter(cfg-system-sztp-security)# authentication-type server-authentication-only


**Removing Configuration**

To revert authentication-type to default:
::

    dnRouter(cfg-system-sztp-security)# no authentication-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
