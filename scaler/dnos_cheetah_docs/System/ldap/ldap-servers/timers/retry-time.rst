system ldap ldap-servers timers retry-time
------------------------------------------

**Minimum user role:** admin

Prevents a failed LDAP server from being retried too soon. If an LDAP server is marked as failed, it will not be used for LDAP requests until the retry time has expired. Once the retry time has expired, the LDAP server may be marked as available to accept new LDAP requests

**Command syntax: retry-time [retry-time]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers timers

**Parameter table**

+------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                                      | Range   | Default |
+============+==================================================================================+=========+=========+
| retry-time | prevent a failed LDAP server from being retried too soon. If a LDAP server is    | 10-3600 | 1200    |
|            | marked as failed, it will not be used for LDAP requests until the retry time has |         |         |
|            | expired. Once the retry time has expired, the LDAP server may be marked as       |         |         |
|            | available to accept LDAP new requests                                            |         |         |
+------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# timers
    dnRouter(cfg-ldap-servers-timers)# retry-time 70


**Removing Configuration**

To revert the retry-time to the default:
::

    dnRouter(cfg-ldap-servers)# no retry-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
