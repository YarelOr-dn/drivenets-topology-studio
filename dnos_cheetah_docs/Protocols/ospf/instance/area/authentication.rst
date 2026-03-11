protocols ospf instance area authentication
-------------------------------------------

**Minimum user role:** operator

Use authentication to guarantee that only trusted devices participate in the area’s routing.
To configure authentication:

**Command syntax: authentication [authentication-type]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Note**

- Authentication is disabled by default

- clear-text - sets "clear-text" as the expected authentication on all area interfaces

- md5 - sets "md5" as the expected authentication on all area interfaces

**Parameter table**

+---------------------+-------------------------------------------------------+----------------+-------------------+
| Parameter           | Description                                           | Range          | Default           |
+=====================+=======================================================+================+===================+
| authentication-type | Set the authentication type that is used in the area. | | clear-text   | no authentication |
|                     |                                                       | | md5          |                   |
|                     |                                                       | | ipsec        |                   |
+---------------------+-------------------------------------------------------+----------------+-------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# authentication-type md5


**Removing Configuration**

To disable authentication requirement:
::

    dnRouter(cfg-ospf-area)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
