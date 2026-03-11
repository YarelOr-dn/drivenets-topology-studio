system icmp
-----------------------------------------------

**Minimum user role:** operator

You can configure ICMP and ICMPv6 replies:

**Command syntax: system icmp**

**Command mode:** config

**Hierarchies**

- system


**Note**

- Notice the change in prompt

.. -  No command returns the all icmp replies configurations to default.


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# icmp
	


	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no icmp

.. **Help line:** configuration per ICMP/ICMPv6 replies.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+

