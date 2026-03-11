interfaces gre-tunnel
---------------------

**Minimum user role:** operator

Generic Routing Encapsulation (GRE) is a tunneling mechanism that encapsulates packets of any protocol inside IP packets delivered to a destination endpoint. The GRE tunnel behaves as a virtual point-to-point connection between the two endpoints (identified as tunnel source and tunnel destination).

To configure a GRE tunnel interface:

**Command syntax: gre-tunnel-[id]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the gre-tunnel interface.

**Parameter table**

+---------------+--------------------------+-----------+-------------+
|               |                          |           |             |
| Parameter     | Description              | Range     | Default     |
+===============+==========================+===========+=============+
|               |                          |           |             |
| ID            | The tunnel identifier    | 0..4      | \-          |
+---------------+--------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# gre-tunnel-0 
	dnRouter(cfg-if-gre-0)# 


**Removing Configuration**

To remove the GRE tunnel interface and all its configurations:
::

	dnRouter(cfg-if)# no gre-tunnel-0


.. **Help line:** configures gre tunnel interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.4        | Command introduced    |
+-------------+-----------------------+
