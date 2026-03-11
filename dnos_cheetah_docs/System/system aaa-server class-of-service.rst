system aaa-server class-of-service
----------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing TACACS+ and RADIUS messages:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system aaa-server

**Note**

- The configuration is global for all outgoing TACACS+ and RADIUS messages.

.. - Configuration is global for all outgoing TACACS+ and RADIUS messages

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
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# class-of-service 12
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-aaa)# no class-of-service 



**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.0    | Command introduced       |
+---------+--------------------------+
| 13.0    | Added support for RADIUS |
+---------+--------------------------+

