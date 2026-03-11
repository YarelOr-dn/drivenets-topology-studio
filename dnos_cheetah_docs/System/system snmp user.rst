system snmp user
-----------------

**Minimum user role:** operator

To configure a user for SNMP and enter the SNMP user configuration mode:

**Command syntax: user [user-name] parameter** [parameter-value]

**Command mode:** config

**Hierarchies**

- system snmp

**Note**

- Notice the change in prompt.

.. - Creation of a user must include auth-type and auth-password

	- password will be displayed as encrypted text. (enc-xxxx)

	- The same password is used for encryption and authentication

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------+-----------+
| Parameter | Description                                                                             | Range     |
+===========+=========================================================================================+===========+
| user-name | Enter a user name. If the user name does not already exist, a new user will be created. | String    |
+-----------+-----------------------------------------------------------------------------------------+-----------+

When creating an SNMP user, you must set the authentication (type of authentication and password are both required) for the user. See system snmp user authentication.

For each user, you can optionally set encryption and view options. The same password is used for authentication and for encryption. See system snmp user encryption and system snmp user view, respectively.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# user MySnmpUser2
	dnRouter(cfg-system-snmp-user)# authentication md5 password enc-#dsddsd546
	dnRouter(cfg-system-snmp-user)# encryption des
	dnRouter(cfg-system-snmp-user)# view MyView

	dnRouter(cfg-system-snmp)# user MySnmpUser3
	dnRouter(cfg-system-snmp-user)# authentication sha
	dnRouter(cfg-system-snmp-user)# password enc-234asds$#5



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-snmp)# no user MySnmpUser1

.. **Help line:** Configure system snmp user authentication

**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 5.1.0   | Command introduced             |
+---------+--------------------------------+
| 6.0     | Applied new hierarchy for SNMP |
+---------+--------------------------------+
| 9.0     | Applied new hierarchy for user |
+---------+--------------------------------+
