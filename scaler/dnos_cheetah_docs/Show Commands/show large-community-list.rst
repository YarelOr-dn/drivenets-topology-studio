show large-community-list
-------------------------

**Minimum user role:** viewer

To display a large community list:



**Command syntax: show large-community-list** [large-community-list-name]

**Command mode:** operational




**Parameter table**

+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter                 | Description                                                                                                                                           |
+===========================+=======================================================================================================================================================+
| large-community-list-name | The name of the large community list to display. If you do not specify an large community list, all large community lists will be displayed.          |
+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show large-community-list

    large-community-list L_COM_1
      rule 10 allow value 65000:100:200
      rule 20 allow value 65000:100:300
    !
    large-community-list L_COM_2
      rule 10 deny regex "65060L:1000|65060l:2000"
    !

	
	dnRouter# show large-community-list

    large-community-list L_COM_1
      rule 10 allow value 65000:100:200
      rule 20 allow value 65000:100:300
    !

	

.. **Help line:** List large-community-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+


