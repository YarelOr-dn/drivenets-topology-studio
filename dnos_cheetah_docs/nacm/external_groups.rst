nacm external-groups
--------------------

**Minimum user role:** admin

When the global switch is set to 'true', the group names reported by the transport layer, for a session, are used together with the locally configured group names to determine the access control rules for the session. When this switch is set to 'false', the group names reported by the transport layer are ignored by the NACM.

**Command syntax: external-groups [enable-external-groups]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter              | Description                                                                      | Range        | Default |
+========================+==================================================================================+==============+=========+
| enable-external-groups | Controls whether the server uses the groups reported by the NETCONF transport    | | enabled    | True    |
|                        | layer when it assigns the user to a set of NACM groups.  If this leaf has the    | | disabled   |         |
|                        | value 'false', any group names reported by the transport layer are ignored by    |              |         |
|                        | the server.                                                                      |              |         |
+------------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# external-groups enabled


**Removing Configuration**

To revert delay to default:
::

    dnRouter(cfg-netconf-nacm)# no external-groups

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
