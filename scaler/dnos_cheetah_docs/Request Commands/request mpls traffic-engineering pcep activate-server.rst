request mpls traffic-engineering pcep activate-server
-----------------------------------------------------

**Minimum user role:** operator

To reconnect idle peers (PCEs):

**Command syntax: request mpls traffic-engineering pcep activate-server** peer [ipv4-address]

**Command mode:** operational

**Parameter table**

+--------------+-------------------------------------------------------------+---------+
| Parameter    | Description                                                 | Range   |
+==============+=============================================================+=========+
| No parameter | The command will cause the system to reconnect to all PCEs. | \-      |
+--------------+-------------------------------------------------------------+---------+
| ipv4-address | The system will reconnect to a specific PCE                 | A.B.C.D |
+--------------+-------------------------------------------------------------+---------+

**Example**
::

	dnRouter# request mpls traffic-engineering pcep activate-server peer 1.1.1.1
	
	dnRouter# request mpls traffic-engineering pcep activate-server 
	

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+