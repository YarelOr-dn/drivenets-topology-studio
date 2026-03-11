system ldap ldap-servers ldap-server priority source-interface
--------------------------------------------------------------

**Minimum user role:** operator

IP address of this interface is used as the source IP address of all outingoing LDAP messages.

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers ldap-server priority

**Parameter table**

+------------------+-----------------------------------------------------------------+---------------------------------------------------------------+----------------------------------------+
| Parameter        | Description                                                     | Range                                                         | Default                                |
+==================+=================================================================+===============================================================+========================================+
| source-interface | The source interface whose IP address is used for LDAP messages | Any interface in the configured VRF with an IPv4/IPv6 address | inband interface in the configured VRF |
+------------------+-----------------------------------------------------------------+---------------------------------------------------------------+----------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# ldap-server priority 5
    dnRouter(cfg-ldap-servers-server)# source-interface lo1


**Removing Configuration**

To remove the source-interface:
::

    dnRouter(cfg-ldap-servers-server)# no source-interface 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
