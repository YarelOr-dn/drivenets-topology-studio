show system tech-support status
-------------------------------

**Minimum user role:** viewer

To display the generation status of the tech-support file:



**Command syntax: show system tech-support status**

**Command mode:** operational



**Note**

- If no tech-support file is currently being generated, information on the last generated tech-support file is displayed.

- The file generation progress includes these steps:

	# step 1 - preparing

	# step 2 - discovering containers

	# step 3 - running scripts on containers

	# step 4 - collecting files on containers

	# step 5 - creating archive



**Example**
::

	dnRouter# show system tech-support status

	Tech-support file generation in progress
	Tech-support file generation started at 13:32:00_30-01-2017, by User_1, running for 5 min
	File name MyTechSupportFile_13:32:00_30-01-2017.tar.gz
	Tech-support partition: total 98761166848, used: 11645157376, free: 87116009472, pct: 11.8% used
	Progress: step 3/5 - running scripts on containers

	
	
	
	


**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 11.2    | Command introduced             |
+---------+--------------------------------+
| 11.5    | Command added to recovery mode |
+---------+--------------------------------+


