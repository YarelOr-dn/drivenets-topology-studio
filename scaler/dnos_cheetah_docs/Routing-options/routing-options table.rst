routing-options table
---------------------

**Minimum user role:** operator

To enter configuration mode for the routing table to which you want to apply a policy (see explanation in routing-options):

**Command syntax: table [table-name]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Notice the change in prompt.

.. - no command returns all table configurations to their default state

**Parameter table**

+------------+----------------------------------------------+---------+
| Parameter  | Description                                  | Range   |
+============+==============================================+=========+
| table-name | The routing table that you want to configure | mpls-nh |
+------------+----------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# table mpls-nh
	dnRouter(cfg-routing-option-mpls-nh)# 
	
	

**Removing Configuration**

To revert all table configuration to the default values:
::

	dnRouter(cfg-routing-option)# no table mpls-nh

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


