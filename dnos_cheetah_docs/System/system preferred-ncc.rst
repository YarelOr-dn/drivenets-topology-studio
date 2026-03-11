system preferred-ncc
--------------------

**Minimum user role:** operator

Up to two NCCs can be set per cluster for redundancy; one active (the preferred NCC) and the other in stand-by. The NCC identification is managed by DNOR. The first NCC that DNOR configures is by default the preferred NCC and receives the ID 0. The other NCC is allocated the ID 1.

During system boot, if both NCCs are available, the preferred NCC is the one that will be selected as the active NCC.

You can manually configure the preferred designation of an NCC.

To set the preferred NCC:

**Command syntax: preferred-ncc [ncc-id]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- This command is not applicable to a standalone NCP. The NCC in a standalone NCP is automatically configured as primary and receives the ID 0. You cannot change this setting.

- Only one NCC per cluster can serve as the preferred NCC. When you configure an NCC as preferred, the other NCC will automatically be stripped of its preferred status.

.. - The factory default preferred NCC number is ncc-id=0. 'no preferred-ncc' command returns the preferred-ncc parameter to the default.

	- For **standalone cluster**, NCC 0 is configured as primary. User cannot change this configuration.

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                                                                                           | Range | Default |
+===========+=======================================================================================================================================================================================================+=======+=========+
| ncc-id    | The identifier of the preferred NCC. If the NCC with the specified ID is not currently the preferred one, it will become the preferred one and it will become the active NCC on the next system boot. | 0..1  | 0       |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# preferred-ncc 1
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no preferred-ncc

.. **Help line:** configure a primary NCC for DNOS cluster. Primary NCC is the one that will be selected as active NCC during system boot (if both NCCs are available).

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


