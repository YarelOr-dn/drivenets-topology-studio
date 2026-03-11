system ldap ldap-server priority bind-dn-timeout
------------------------------------------------

**Minimum user role:** admin

To set the binding timeout in seconds:

**Command syntax: bind-dn-timeout [bind-dn-timeout]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-server priority

**Parameter table**

+-----------------+------------------------------------+--------+---------+
| Parameter       | Description                        | Range  | Default |
+=================+====================================+========+=========+
| bind-dn-timeout | Set the binding timeout in seconds | 1..1000| 5       |
+-----------------+------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-server priority 1
    dnRouter(cfg-system-ldap-server)# bind-dn-timeout 60


**Removing Configuration**

To revert bind-timeout to default:
::

    dnRouter(cfg-system-ldap-server)# no bind-dn-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
