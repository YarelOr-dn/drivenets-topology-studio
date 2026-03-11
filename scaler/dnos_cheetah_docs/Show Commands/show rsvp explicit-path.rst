show rsvp explicit-path
-----------------------

**Minimum user role:** viewer

To display the configured explicit-paths (see rsvp explicit-path):

**Command syntax: show rsvp explicit-path** [path-name]

**Command mode:** operational


**Parameter table**

+-----------+----------------------------------------------------------+
| Parameter | Description                                              |
+===========+==========================================================+
| no filter | Displays all configured RSVP explicit-paths.             |
+-----------+----------------------------------------------------------+
| path-name | Filter the displayed information by a specific path name |
+-----------+----------------------------------------------------------+

**Example**
::

	dnRouter# show rsvp explicit-path
	Name: test
	 1  1.1.1.1          loose
	
	Name: test2
	 1  14.14.14.2       strict
	 10 45.45.45.2       strict
	 13 56.56.56.2       strict
	
	dnRouter# show rsvp explicit-path test2
	Name: test2
	 1  14.14.14.2       strict
	 10 45.45.45.2       strict
	 13 56.56.56.2       strict
	
	


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+


