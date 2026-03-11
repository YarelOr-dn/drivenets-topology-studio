system ldap ldap-servers timers hold-down
-----------------------------------------

**Minimum user role:** admin

The hold-down timer is triggered when all the LDAP servers are found to be in an unavailable state. A hold-down state prevents all LDAP requests from being sent to any LDAP servers.The purpose of this delay is to limit unnecessary delays due to LDAP requests being sent to unavailable servers incurring the connection timeout. If the delay is set to zero, the hold down timer is disabled and LDAP requests are sent to servers. To configure the hold-down timer:

**Command syntax: hold-down [hold-down]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers timers

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| hold-down | The hold-down timer is triggered when all LDAP servers are found to be in an     | 10-1200 | 600     |
|           | unavailable state. Hold-down state prevents all LDAP requests from being sent to |         |         |
|           | any LDAP servers.The purpose of this delay is to limit unnecessary delays due to |         |         |
|           | LDAP requests being sent to unavailable servers incurring the connection         |         |         |
|           | timeout. If the delay is set to zero, the hold down timer is disabled and LDAP   |         |         |
|           | requests are sent to servers                                                     |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# timers
    dnRouter(cfg-ldap-servers-timers)# hold-down 70


**Removing Configuration**

To revert the hold-down to the default:
::

    dnRouter(cfg-ldap-servers)# no hold-down

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
