system management vrf static 
----------------------------

**Minimum user role:** operator

To enter management static route configuration mode:

**Command syntax: static**

**Command mode:** config

**Hierarchies**

- system management


**Note**

- Notice the change in prompt

.. - "no static" removes all static routes from all static routes from management interface


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static
	dnRouter(cfg-mgmt-vrf-static)#


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-mgmt)# no static



**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 10.0    | Command introduced     |
+---------+------------------------+
| 13.0    | Updated command syntax |
+---------+------------------------+

