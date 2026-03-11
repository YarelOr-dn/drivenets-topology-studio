ldp address-family label explicit-null
--------------------------------------

**Minimum user role:** operator

Assign explicit-null (label 0) to local bindings. Label 0 indicates that the label stack must be 'popped' and the packet is then forwarded based on the IP header, by default it is implicit null (Label 3):

**Command syntax: label explicit-null [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family

.. **Note**

.. - label explicit-null is disabled by default

**Parameter table**

+----------------+-------------------------------------------------+-------------+-------------+
|                |                                                 |             |             |
| Parameter      | Description                                     | Range       | Default     |
+================+=================================================+=============+=============+
|                |                                                 |             |             |
| admin-state    | Administratively set the label explicit-null    | Enabled     | Disabled    |
|                |                                                 |             |             |
|                |                                                 | Disabled    |             |
+----------------+-------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# label explicit-null enabled

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# label explicit-null disabled

**Removing Configuration**

To revert to the default configuration:
::

	dnRouter(cfg-protocols-ldp-afi)# no label explicit-null

.. **Help line:** Configure explicit-null advertisement

**Command History**

+-------------+--------------------------------------------------+
|             |                                                  |
| Release     | Modification                                     |
+=============+==================================================+
|             |                                                  |
| 6.0         | Command introduced                               |
+-------------+--------------------------------------------------+
|             |                                                  |
| 13.0        | Added admin-state setting to command syntax      |
+-------------+--------------------------------------------------+