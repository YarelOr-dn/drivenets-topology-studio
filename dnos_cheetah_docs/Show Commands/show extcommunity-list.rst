show extcommunity-list
----------------------

**Minimum user role:** viewer

To display an extended community list:



**Command syntax: show extcommunity-list** [extcommunity-list-name]

**Command mode:** operational




**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter           | Description                                                                                                                                           |
+=====================+=======================================================================================================================================================+
| community-list-name | The name of the extended community list to display. If you do not specify an extended community list, all extended community lists will be displayed. |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show extcommunity-list
	extcommunity-list CL_RT_13979:100497:
	extcommunity-list CL_RT_13979:100497
	  rule 10 allow rt value 13979:100497
	!
	
	extcommunity-list CL_RT_13979:100499:
	extcommunity-list CL_RT_13979:100499
	  rule 10 allow rt value 13979:100499
	!
	
	dnRouter# show extcommunity-list CL_RT_13979:100499
	extcommunity-list CL_RT_13979:100499:
	extcommunity-list CL_RT_13979:100499
	  rule 10 allow rt value 13979:100499
	!
		
	

.. **Help line:** List extcommunity-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+


