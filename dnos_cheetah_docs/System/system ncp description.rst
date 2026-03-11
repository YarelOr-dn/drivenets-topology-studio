system ncp description
----------------------

**Minimum user role:** operator

To provide a description for the NCP:

**Command syntax: ncp [ncp-id] description [description]**

**Command mode:** config

**Hierarchies**

- system ncp

.. **Note**

	- no command returns the ncp description to its default. For ncp case its "dn-ncp-0" etc

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+----------+
| Parameter   | Description                                                                                                                            | Range  | Default  |
+=============+========================================================================================================================================+========+==========+
| description | Free text describing the NCP.                                                                                                          | string | dn-ncp-0 |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example: |        |          |
|             | ... description "My long description"                                                                                                  |        |          |
|             | ... description My_long_description                                                                                                    |        |          |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 1 
	dnRouter(cfg-system-ncp-1)# description my_desc
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ncp-1)# no description

.. **Help line:** configure an ncp description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


