request segment-routing pcep activate-server
--------------------------------------------

**Minimum user role:** operator

To reconnect idle Segement-routing PCEs peers:

**Command syntax: request segment-routing pcep activate-server** peer [ipv4-address]

**Command mode:** operational

**Parameter table**

+--------------+-------------------------------------------------------------+---------+
| Parameter    | Description                                                 | Range   |
+==============+=============================================================+=========+
| No parameter | This will cause the system to reconnect to all PCEs.        | \-      |
+--------------+-------------------------------------------------------------+---------+
| ipv4-address | The system will reconnect to a specific PCE                 | A.B.C.D |
+--------------+-------------------------------------------------------------+---------+

**Example**
::

	dnRouter# request segment-routing pcep activate-server peer 1.1.1.1

	dnRouter# request segment-routing pcep activate-server


.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
