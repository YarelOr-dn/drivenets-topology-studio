show as-path-list
-----------------

**Minimum user role:** viewer

To display an as-path access-list:


**Command syntax: show as-path-list** [as-path-access-list-name]

**Command mode:** operational


**Parameter table**

+--------------------+-------------------------------+--------------------------------------------------------------------------------------+
| Parameter          | Description                   | Range                                                                                |
+====================+===============================+======================================================================================+
| As-path-list-name: | The name of the as-path list. | 1..25 characters. If you do not specify a specific list, all lists will be displayed |
+--------------------+-------------------------------+--------------------------------------------------------------------------------------+


**Example**
::

	dnRouter# show as-path-list
	as-path access-list AS_MARTIAN_ASNS:
	 as-path access-list AS_MARTIAN_ASNS
	    rule 10 allow passes-through 0
	    rule 20 allow passes-through 23456
	    rule 30 allow passes-through 64496-131071
	    rule 40 allow passes-through 4200000000-4294967295
	 !
	
	
	as-path access-list AS_MARTIAN_ASNS:
	 as-path access-list AS_STANDARD_ASNS
	    rule 10 allow passes-through 174
	    rule 20 allow passes-through 209
	    rule 30 allow passes-through 701
	    rule 40 allow passes-through 1239
	    rule 50 allow passes-through 2914
	    rule 60 allow passes-through 3356
	    rule 70 allow passes-through 3549
	    rule 80 allow passes-through 3561
	    rule 90 allow passes-through 5511
	    rule 100 allow passes-through 6461
	    rule 110 allow passes-through 7922
	  !
	
	
	dnRouter# show as-path-list AS_MARTIAN_ASNS
	as-path access-list AS_MARTIAN_ASNS:
	 as-path access-list AS_MARTIAN_ASNS
	    rule 10 allow passes-through 0
	    rule 20 allow passes-through 23456
	    rule 30 allow passes-through 64496-131071
	    rule 40 allow passes-through 4200000000-4294967295
	 !
	
	

.. **Help line:** Displays an as-path access-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+



