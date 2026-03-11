system icmp unreachable
-----------------------

**Minimum user role:** operator

Configuration of ICMP/ICMPv6 unreachable replies.

To configure icmp unreachable replies:

**Command syntax: icmp unreachable**

**Command mode:** config

**Hierarchies**

- system icmp


.. **Note**

	- No command returns the icmp unreachable configuration to default.


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# icmp
	dnRouter(cfg-system-icmp)# unreachable


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-icmp)# no unreachable

.. **Help line:** configuration per ICMP/ICMPv6 unreachable replies.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


