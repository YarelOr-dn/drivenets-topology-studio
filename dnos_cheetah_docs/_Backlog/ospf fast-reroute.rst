ospf fast-reroute
-----------------

**Minimum user role:** operator

OSPF Loop-Free Alternate (LFA) Fast Reroute (FRR) allows OSPF to quickly switch to a backup path when a primary path fails. Without LFA FRR, OSPF has to re-run SPF to find a new path when the primary path fails. With LFA FRR, OSPF pre-computes a backup path and installs the backup next hop in the forwarding table.

You can:

•	Globally enable fast reroute for the OSPF protocol. See below.

•	Set an interface as a valid candidate for loop-free alternate calculation.

To enable/disable fast reroute globally for the OSPF protocol:

**Command syntax: fast-reroute [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf

.. **Note**

 - no command returns fast-reroute to its default disabled value.



**Parameter table**

+----------------+-----------------------------------------------------+-------------+-------------+
|                |                                                     |             |             |
| Parameter      | Description                                         | Range       | Default     |
+================+=====================================================+=============+=============+
|                |                                                     |             |             |
| admin-state    | Enable/Disable fast reroute per prefix for OSPF     | Enabled     | Disabled    |
|                |                                                     |             |             |
|                |                                                     | Disabled    |             |
+----------------+-----------------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ospf
	dnRouter(cfg-protocols-ospf)# fast-reroute enabled

**Removing Configuration**

To return the fast-reroute to its default value: 
::

	dnRouter(cfg-protocols-ospf)# no fast-reroute


.. **Help line:** Enables fast-reroute per prefix for OSPF

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.6        | Command introduced    |
+-------------+-----------------------+


