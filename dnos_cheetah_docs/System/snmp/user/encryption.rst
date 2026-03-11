system snmp user encryption
---------------------------

**Minimum user role:** operator

To configure SNMP user encryption

**Command syntax: encryption [type]**

**Command mode:** config

**Hierarchies**

- system snmp user

**Note**
- validation authentication(md5/sha) **MUST** be configured on the user for encryption to be applied. a warning should be displayed to the user in this case
- no command removes the encryption paramater

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| type      | The encrypted password. If you do not set an encrypted password, you will be     | | aes   | \-      |
|           | prompted to enter a clear password and verify it.                                | | des   |         |
|           | When typing a clear password, the password will not be displayed in the CLI      |         |         |
|           | terminal. The password format must match the encrypted format as displayed in    |         |         |
|           | "show config".                                                                   |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# user MySnmpUser2
    dnRouter(cfg-system-snmp-user)# encryption des
    dnRouter(cfg-system-snmp)# user MySnmpUser3
    dnRouter(cfg-system-snmp-user)# encryption aes


**Removing Configuration**

To revert the router-id to default
::

     dnRouter(cfg-system-snmp-user)# no encryption

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
