system snmp user authentication password
----------------------------------------

**Minimum user role:** operator

To configure the SNMP user authentication algorithm and the password:

**Command syntax: authentication [type] password [enc-password]**

**Command mode:** config

**Hierarchies**

- system snmp user

**Note**
- User configuration must include include auth-type and auth-password
- password length must be a minimum of 8 characters
- password will be displayed as encrypted text. (enc-xxxx)
- validation. password should be validated to avoid user errors
- The same password is used for encryption and authentication
- it is not possible to remove user encryption

**Parameter table**

+--------------+-----------------------------------------------------------------------------+---------+---------+
| Parameter    | Description                                                                 | Range   | Default |
+==============+=============================================================================+=========+=========+
| type         | To configure SNMP user encryption                                           | | md5   | \-      |
|              |                                                                             | | sha   |         |
+--------------+-----------------------------------------------------------------------------+---------+---------+
| enc-password | Localized secret specified as a list of colon-specified hexadecimal octets. | \-      | \-      |
+--------------+-----------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system snmp
    dev-dnRouter(cfg-system-snmp)# user snmp-test authentication sha password
    Enter password
    Enter password for verification


**Removing Configuration**

To remove the configuration:
::

    dev-dnRouter(cfg-system-snmp)# no user snmp-test authentication sha password

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
