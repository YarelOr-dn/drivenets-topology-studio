system ncf description
----------------------

**Minimum user role:** operator

To provide a description for the NCF:

**Command syntax: ncf [ncf-id] description [description]**

**Command mode:** config

**Hierarchies**

- system ncf


.. **Note**

	- no command returns the ncf description to its default. For ncf case its "dn-ncf-0" etc

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+----------+
| Parameter   | Description                                                                                                                            | Range  | Default  |
+=============+========================================================================================================================================+========+==========+
| description | Free text describing the NCF.                                                                                                          | string | dn-ncf-0 |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example: |        |          |
|             | ... description "My long description"                                                                                                  |        |          |
|             | ... description My_long_description                                                                                                    |        |          |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncf 1 
	dnRouter(cfg-system-ncf-1)# description my_desc
	
	


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ncf-1)# no description

.. **Help line:** configure an ncf description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


