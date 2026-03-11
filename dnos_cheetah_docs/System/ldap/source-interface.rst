system ldap source-interface
----------------------------

**Minimum user role:** admin

IP address of this interface is used as source IP address of all outingoing LDAP messages

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system ldap

**Parameter table**

+------------------+-----------------------------------------------------------------+----------------------------------------------------------------------------------+--------------------------------------------+
| Parameter        | Description                                                     | Range                                                                            | Default                                    |
+==================+=================================================================+==================================================================================+============================================+
| source-interface | The source interface whose IP address is used for LDAP messages | Any interface in the default VRF with an IPv4/IPv6 address, except GRE tunnel    | system in-band-management source-interface |
|                  |                                                                 | interfaces                                                                       |                                            |
+------------------+-----------------------------------------------------------------+----------------------------------------------------------------------------------+--------------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# source-interface ge100-0/0/0


**Removing Configuration**

To revert source-interface to default:
::

    dnRouter(cfg-system-ldap)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
