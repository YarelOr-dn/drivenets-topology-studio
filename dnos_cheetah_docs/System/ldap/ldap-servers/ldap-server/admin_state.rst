system ldap ldap-servers ldap-server priority admin-state
---------------------------------------------------------

**Minimum user role:** admin

To configure the desired administrative state of the LDAP server:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers ldap-server priority

**Parameter table**

+-------------+--------------------------------------+--------------+---------+
| Parameter   | Description                          | Range        | Default |
+=============+======================================+==============+=========+
| admin-state | The desired state of the LDAP server | | enabled    | enabled |
|             |                                      | | disabled   |         |
+-------------+--------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# ldap-server priority 1
    dnRouter(cfg-ldap-servers-server)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-ldap-servers-server)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
