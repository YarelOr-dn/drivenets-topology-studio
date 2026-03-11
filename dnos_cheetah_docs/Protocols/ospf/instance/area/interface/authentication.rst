protocols ospf instance area interface authentication
-----------------------------------------------------

**Minimum user role:** operator

To configure the OSPF authentication method for an OSPF enabled interface:

**Command syntax: authentication [authentication-type]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- The authentication default is determined by the area authentication configuration.

- The OSPF authentication is disabled by default.

- clear-text - clear-text is the expected authentication on all area interfaces.

- md5 - md5 is the expected authentication on all area interfaces.

- no authentication - return authentication to the default state according to the area authentication settings.

**Parameter table**

+---------------------+-------------------------------------------------------+----------------+-------------------+
| Parameter           | Description                                           | Range          | Default           |
+=====================+=======================================================+================+===================+
| authentication-type | Set the authentication type that is used in the area. | | clear-text   | no authentication |
|                     |                                                       | | md5          |                   |
+---------------------+-------------------------------------------------------+----------------+-------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# authentication clear-text
    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1
    dnRouter(cfg-ospf-area-if)# authentication md5


**Removing Configuration**

To return the authentication type to its default value:
::

    dnRouter(cfg-ospf-area-if)# no authentication 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
