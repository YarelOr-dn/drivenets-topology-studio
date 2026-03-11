show community-list
-------------------

**Minimum user role:** viewer

To display a community list:

**Command syntax: show community-list** [community-list-name]

**Command mode:** operational




**Parameter table**

+---------------------+---------------------------------------------------------------------------------------------------------------------------+
| Parameter           | Description                                                                                                               |
+=====================+===========================================================================================================================+
| community-list-name | The name of the community list to display. If you do not specify a community list, all community lists will be displayed. |
+---------------------+---------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show community-list
	community-list CL_1000:
	community-list CL_1000
	  rule 10 allow value 65060:1000
	!
	
	
	community-list CL_2000:
	community-list CL_2000
	  rule 10 allow value 65060:2000
	!
	
	
	
	dnRouter# show community-list CL_2000
	community-list CL_2000:
	community-list CL_2000
	  rule 10 allow value 65060:2000
	!
	
	
	

.. **Help line:** List community-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+


