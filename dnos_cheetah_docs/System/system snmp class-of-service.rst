system snmp class-of-service
----------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing SNMP sessions:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system snmp

.. **Note**

	- Configuration is global for all outgoing snmp applications (trap-server output etc).

	- Value is the dscp value on the ip header

**Parameter table**

+------------+---------------------------------------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                                                 | Range | Default |
+============+=============================================================================================+=======+=========+
| dscp-value | The DSCP value that is used in the IP header to classify the packet and give it a priority. | 0..56 | 16      |
+------------+---------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# snmp
	dnRouter(cfg-system-snmp)# class-of-service 54
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-snmp)# no class-of-service

.. **Help line:** Configure system snmp class of service value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


