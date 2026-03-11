interfaces lo 
--------------

**Minimum user role:** operator

A loopback interface is valid only if an IP address (IPv4 or IPv6) is configured for it. To create a loopback interface or enter an existing loopback interface's configuration mode:

**Command syntax: lo<id>**

**Command mode:** config

**Hierarchies**

- interfaces 

**Note**

- The command is applicable to loopback interfaces.
- Loopback interface can be created either with or without adding any parameter.

..
	**Internal Note**

	Validations:

	-  Loopback ipv4 interface can be configured only with /32

	-  Loopback ipv6 interface can be configured only with /128


**Parameter table**

+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|               |                                                                                                                                                                                                                                          |             |             |
| Parameter     | Description                                                                                                                                                                                                                              | Range       | Default     |
+===============+==========================================================================================================================================================================================================================================+=============+=============+
|               |                                                                                                                                                                                                                                          |             |             |
| lo-id         | The loopback interface identifier. If the ID does   not already exist, this will create a loopback interface with the specific   identifier. If exists, this will enter the configuration mode for the   specific loopback interface.    | 0..65535    | \-          |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# lo0
	dnRouter(cfg-if-lo0)# 


**Removing Configuration**

To delete the lo0 interface:
::

	dnRouter(cfg-if)# no lo0 


.. **Help line:**

**Command History**

+-------------+-------------------------------------------------------+
|             |                                                       |
| Release     | Modification                                          |
+=============+=======================================================+
|             |                                                       |
| 5.1.0       | Command introduced                                    |
+-------------+-------------------------------------------------------+
|             |                                                       |
| 6.0         | Changed syntax from interface to interfaces           |
|             |                                                       |
|             | Applied new hierarchy                                 |
+-------------+-------------------------------------------------------+
|             |                                                       |
| 7.0         | Removed the keyword "interface" from   the syntax.    |
+-------------+-------------------------------------------------------+