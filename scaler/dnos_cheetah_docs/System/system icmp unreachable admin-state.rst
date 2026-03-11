system icmp unreachable admin-state
-----------------------------------------------

**Minimum user role:** operator

Enables/disables path-mtu-discovery (PMTUD) for ICMP/ICMPv6 replies to the source of data-plane messages that are dropped due to exceeding the MTU.

To configure icmp unreachable admin-state:

**Command syntax: icmp unreachable admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

-  system icmp unreachable


**Note**

- Notice the change in prompt.

.. -  No command returns the state to default.

**Parameter table**

+-------------+-------------------------------------------------------------------+----------+---------------+
| Parameter   | Description                                                       | Range    | Default       |
+=============+===================================================================+==========+===============+
| admin-state | Administratively enable or disable PMTUD for ICMP/ICMPv6 replies. | Enabled  | Enabled       |
|             |                                                                   | Disabled |               |
+-------------+-------------------------------------------------------------------+----------+---------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# icmp
	dnRouter(cfg-system-icmp)# unreachable
	dnRouter(system-icmp-unrechable)# admin-state disabled





**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(system-icmp-unrechable)# no admin-state

.. **Help line:** enable/disable path-mtu-discovery (aka PMTUD) ICMP/ICMPv6 reply to source of the data-plane messages that are dropped due to exceeding MTU. Up to 1000 ICMP and 1000 ICMPv6 replies per seconds are supported per NCP.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
