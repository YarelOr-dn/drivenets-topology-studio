system management vrf  
---------------------

**Minimum user role:** operator

To enter management vrf configuration level:

**Command syntax: vrf [vrf]**

**Command mode:** config

**Hierarchies**

- system management


**Note**

- Notice the change in prompt

.. - "no static" removes all configuration from management vrf

**Parameter table**

+-----------+-----------------------------+-----------------------------------+---------+
| Parameter | Description                 | Range                             | Default |
+===========+=============================+===================================+=========+
| vrf       | Displays the management vrf | mgmt0, mgmt-ncc-0, mgmt-ncc-1     | \-      |
+-----------+-----------------------------+-----------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system 
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)#


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-mgmt)# no mgmt0


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


