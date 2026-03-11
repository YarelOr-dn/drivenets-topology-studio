system ldap ldap-servers ldap-server priority address
-----------------------------------------------------

**Minimum user role:** admin

To configure the IP address of the ldap-server (IPv4/IPv6 addresses or FQDN/PQDN hostnames are supported):

**Command syntax: address [address]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers ldap-server priority

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| address   | IP address of ldap-server. IPv4/IPv6 addresses or FQDN/PQDN hostnames are        | \-    | \-      |
|           | suported                                                                         |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# ldap-server priority 5
    dnRouter(cfg-ldap-servers-server)# address 10.10.73.13


**Removing Configuration**

To revert the ldap-server address to the default:
::

    dnRouter(cfg-ldap-servers-server)# no address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
