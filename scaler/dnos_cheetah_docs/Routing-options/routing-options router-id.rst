routing-options router-id
-------------------------

**Minimum user role:** operator

To manually set the router-id to be used by the routing protocols:

**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- routing-options

.. **Note**

	- used be default vrf

	- no command returns router-id to default value

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------+---------+-------------------------------------------------------------+
| Parameter | Description                                                                                                                   | Range   | Default                                                     |
+===========+===============================================================================================================================+=========+=============================================================+
| router-id | Set the network unique router ID. This ID will serve as the default ID for all routing protocols, unless otherwise specified. | A.B.C.D | The highest IPv4 address from any active loopback interface |
+-----------+-------------------------------------------------------------------------------------------------------------------------------+---------+-------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# router-id 1.1.1.1
	
	
	

**Removing Configuration**

To remove the router-id configuration: 
::

	dnRouter(cfg-routing-option)# no router-id

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 6.0     | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 11.0    | Moved from the Protocols hierarchy to the Routing-options hierarchy. |
+---------+----------------------------------------------------------------------+


