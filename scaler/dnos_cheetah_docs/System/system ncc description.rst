system ncc description
----------------------

**Minimum user role:** operator

To provide a description for the NCC:

**Command syntax: ncc [ncc-id] description [description]**

**Command mode:** config

**Hierarchies**

- system 


.. **Note**

	- no command returns the ncc description to its default. For ncc case its "dn-ncc-0" or "dn-ncc-1"

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+---------------------------------------+
| Parameter   | Description                                                                                                                            | Range  | Default                               |
+=============+========================================================================================================================================+========+=======================================+
| description | Free text describing the NCC.                                                                                                          | string | dn-ncc-1 (the ID of the selected NCC) |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example: |        |                                       |
|             | ... description "My long description"                                                                                                  |        |                                       |
|             | ... description My_long_description                                                                                                    |        |                                       |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+---------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncc 1 
	dnRouter(cfg-system-ncc-1)# description my_desc
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ncc-1)# no description

.. **Help line:** configure an ncc description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


