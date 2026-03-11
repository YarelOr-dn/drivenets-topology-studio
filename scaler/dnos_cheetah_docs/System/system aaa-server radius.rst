system aaa-server radius
------------------------

**Minimum user role:** operator

To define a remote RADIUS server, enter AAA RADIUS configuration mode:


**Command syntax:** radius

**Command mode:** config

**Hierarchies**

- system aaa-server radius


**Note**

- Notice the change in prompt.

.. - "no radius" removes RADIUS authentication configuration


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius
	dnRouter(cfg-system-aaa-radius)# 

	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-aaa)# no radius

.. **Help line:** Configure authentication via RADIUS protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+

