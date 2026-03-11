show mpls traffic-engineering diffserv-te
-----------------------------------------

**Minimum user role:** viewer

To display the diffserv-te bandwidth model and te-class to tunnel class and priority mapping:



**Command syntax: show mpls traffic-engineering diffserv-te**

**Command mode:** operational



**Note**

- See mpls traffic-engineering diffserv-te for information on diffserv-te.


**Example**
::

	dnRouter# show mpls traffic-engineering diffserv-te
	Bandwidth model: Russian dolls model
	TE class     Class-Type          Priority
	te0          ct0                 0
	te1          ct0                 1
	te2          ct1                 0
	te3          ct1                 1
	te4          ct0                 2
	te5          ct1                 2
	te6          ct0                 6
	te7          ct0                 7
	
	

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

