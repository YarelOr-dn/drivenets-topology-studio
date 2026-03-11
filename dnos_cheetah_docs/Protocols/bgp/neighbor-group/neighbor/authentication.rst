protocols bgp neighbor-group neighbor authentication md5 password
-----------------------------------------------------------------

**Minimum user role:** operator

To set a password for authenticating the neighbor, peer group neighbors, or the neighbor in a peer group:

**Command syntax: authentication md5 password [secret]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor
- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- Changing the configuration will cause the BGP session to restart.

- If you do not specify a password, enter the password of the neighbor BGP router in clear text. The password is then encrypted and from then on will be displayed as encrypted. You can copy the encrypted password and use it as the enc-password. When typing a clear password, the password is not displayed in the CLI terminal.

- The clear text password provided in the CLI is hashed with the md5 hash. As the md5 hash is not strong enough and can be broken, the FERNET algorithm is applied to the md5 hash before it is stored in the DNOS database.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| secret    | set a password for authentication encrypted secret password string for the       | \-    | \-      |
|           | neighbor bgp. if the user enters a clear-text password, the password is then     |       |         |
|           | encrypted by the system and saved in secret argument. if the user specified      |       |         |
|           | 'secret' (already encrypted string) save the string in secret                    |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# authentication md5 password
    Enter password
    Enter password for verifications

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.2.2
    dnRouter(cfg-protocols-bgp-neighbor)# authentication md5 password enc-!U2FsdGVkX1+

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# authentication md5 password
    Enter password
    Enter password for verification

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# authentication md5 password
    Enter password
    Enter password for verification
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# authentication md5 password enc-!U2FsdGVkX1+qG


**Removing Configuration**

To remove the password configuration:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no authentication md5

::

    dnRouter(cfg-protocols-bgp-group)# no authentication md5

::

    dnRouter(cfg-bgp-group-neighbor)# no authentication md5

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
