system tcp
-----------------------------------------------

**Minimum user role:** operator

The Transmission Control Protocol (TCP) is used to connect network devices over the internet. TCP defines the behavior of data exchange over the internet. It determines the way data is addressed, transmitted and received.

To enter TCP configuration mode:

**Command syntax: tcp**

**Command mode:** config

**Hierarchies**

- system 

**Note**

- Notice the change in prompt.

.. -  No command returns the all tcp configurations to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# tcp
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no tcp

.. **Help line:** configuration per tcp for control protocols.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


