system ncp port-select
----------------------

**Minimum user role:** operator

Sets the port group to select either the QSFP28 100G ge100 ports 0 and 21 or all SFP-DD 10G ge10 ports.

**Command syntax: port-select [port-select]**

**Command mode:** config

**Hierarchies**

- system ncp

**Note**

- The command is applicable only to NCP-40C8CD with multiplexing functionality between network QSFP28 ports 0 and 21 and all SFP-DD 10G ge10 ports.
- The command is applicable only when non-selected port(s) are in admin-state disable state.

**Parameter table**

+-------------+------------------------+--------------------+---------+
| Parameter   | Description            | Range              | Default |
+=============+========================+====================+=========+
| port-select | Select available ports | | ge100-0-and-21   | \-      |
|             |                        | | ge10-all         |         |
+-------------+------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 0
    dnRouter(cfg-system-ncp-0)# port-select ge100-0-and-21


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-system-ncp-0)# no port-select

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
