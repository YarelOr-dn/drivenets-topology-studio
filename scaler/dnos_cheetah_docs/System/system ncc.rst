system ncc
----------

**Minimum user role:** operator

Up to two NCCs can be set per cluster for redundancy; one active (the primary NCC) and the other in stand-by. The NCC identification is managed by DNOR. The first NCC that DNOR configures is by default the primary NCC and receives the ID 0. The other NCC is allocated the ID 1.

To enter the configuration mode of an NCC:

**Command syntax: ncc [ncc-id]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- NCC 1 is not applicable to a standalone NCP.

- Notice the change in prompt.

.. - no command returns the ncc entity to its default.

	- For **standalone cluster**, NCC-1 is not configured.

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                | Range | Default |
+===========+============================================================================================================+=======+=========+
| ncc-id    | The identifier of the NCC. The ID is unique within the cluster. Up to 2 NCC per cluster can be configured. | 0..1  | \-      |
+-----------+------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncc 1 
	dnRouter(cfg-system-ncc-1)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no ncc 1

.. **Help line:** configure an ncc for DNOS cluster

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


