system ldap class-of-service
----------------------------

**Minimum user role:** admin

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority. To configure a CoS for all outgoing LDAP messages:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system ldap

**Parameter table**

+------------------+-------------------------------------+-------+---------+
| Parameter        | Description                         | Range | Default |
+==================+=====================================+=======+=========+
| class-of-service | Differentiated Services Code Point. | 0-56  | 16      |
+------------------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# class-of-service 15


**Removing Configuration**

To revert the class-of-service to the default value:
::

    dnRouter(cfg-system-ldap)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
