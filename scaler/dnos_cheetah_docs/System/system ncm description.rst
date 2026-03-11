system ncm description
----------------------

**Minimum user role:** operator

To provide a description for the NCM:

**Command syntax: ncm [ncm-id] description [description]**

**Command mode:** config

**Hierarchies**

- system


.. **Note**

	- no command returns the ncm description to its default. For ncm case its "dn-ncm-A0" etc

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+------------------------------------------+
| Parameter   | Description                                                                                                                            | Range  | Default                                  |
+=============+========================================================================================================================================+========+==========================================+
| description | Free text describing the NCM.                                                                                                          | string | dn-ncm-<ID> (the ID of the selected NCM) |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example: |        |                                          |
|             | ... description "My long description"                                                                                                  |        |                                          |
|             | ... description My_long_description                                                                                                    |        |                                          |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------+--------+------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncm A0 
	dnRouter(cfg-system-ncm-A0)# description my_desc
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ncm-A0)# no description

.. **Help line:** configure an ncm description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


