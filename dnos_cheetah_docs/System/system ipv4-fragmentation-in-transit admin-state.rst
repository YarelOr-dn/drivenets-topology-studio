system ipv4-fragmentation-in-transit admin-state
------------------------------------------------

**Minimum user role:** operator

Use this command to fragment transit data packets when the MTU on the ingress L3 interface is larger than the MTU on the egress L3 interface.

Enables/disables IPv4 packet fragmentation:

**Command syntax: ipv4-fragmentation-in-transit admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ipv4


.. **Note**

	- No command reverts the ipv4 fragmentation admin-state to default.

**Parameter table**

+-------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                                                                                                                                                    | Range    | Default  |
+=============+================================================================================================================================================================================================================================+==========+==========+
| admin-state | The administrative state of the IPv4 fragmentation feature. When enabled, data packets larger than the size allowed by the egress port will be fragmented. When disabled, packets larger than the allowed MTU will be dropped. | Enabled  | Disabled |
|             |                                                                                                                                                                                                                                | Disabled |          |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ipv4-fragmentation-in-transit admin-state enabled

	dnRouter(cfg-system)# ipv4-fragmentation-in-transit admin-state disabled


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no ipv4-fragmentation-in-transit admin-state

.. **Help line:** Enable/disable IPv4 packet fragmentation in transit.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+

