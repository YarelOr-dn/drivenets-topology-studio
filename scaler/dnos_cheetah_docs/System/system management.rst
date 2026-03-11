system management 
------------------

**Minimum user role:** operator

To enter the system management configuration mode:

**Command syntax: management**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt.

.. - "no management" - remove all configuration under management


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management 
	dnRouter(cfg-system-mgmt)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no management


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


