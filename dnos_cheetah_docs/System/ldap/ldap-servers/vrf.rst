system ldap ldap-server priority vrf
------------------------------------

**Minimum user role:** admin

To configure the name of the vrf:

**Command syntax: vrf [vrf]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-server priority

**Parameter table**

+-----------+----------------------+----------------+---------+
| Parameter | Description          | Range          | Default |
+===========+======================+================+=========+
| vrf       | The name of the vrf. | string         | default |
|           |                      | length 1..255  |         |
+-----------+----------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-server priority 5
    dnRouter(cfg-system-ldap-server)# vrf mgmt0


**Removing Configuration**

To remove the vrf:
::

    dnRouter(cfg-system-ldap-server)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
