clear mpls traffic-engineering pcep counters
--------------------------------------------

**Minimum user role:** operator

To reset PCEP session counters:

**Command syntax: clear mpls traffic-engineering pcep counters** peer [ipv4-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - set "peer [ipv4-address]" to reset counters for a specific peer


**Parameter table:**

+-----------------+----------------------------------------------------+-----------+-------------+
|                 |                                                    |           |             |
| Parameter       | Description                                        | Range     | Default     |
+=================+====================================================+===========+=============+
|                 |                                                    | A.B.C.D   |             |
| ipv4-address    | Clear PCEP counters for the specified peer only    |           | \-          |
+-----------------+----------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# clear mpls traffic-engineering pcep counters 
	dnRouter# clear mpls traffic-engineering pcep counters peer 1.1.1.1



**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+