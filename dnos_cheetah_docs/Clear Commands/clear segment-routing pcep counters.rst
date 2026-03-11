clear segment-routing pcep counters
-----------------------------------

**Minimum user role:** operator

To reset the SR-TE PCEP session counters:

**Command syntax: clear segment-routing pcep counters** peer [ipv4-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - set "peer [ipv4-address]" to reset counters for a specific peer


**Parameter table:**

+-----------------+----------------------------------------------------+-----------+-------------+
| Parameter       | Description                                        | Range     | Default     |
+=================+====================================================+===========+=============+
| ipv4-address    | Clear PCEP counters for the specified peer only    | A.B.C.D   | \-          |
+-----------------+----------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# clear segment-routing pcep counters
	dnRouter# clear segment-routing pcep counters peer 1.1.1.1



**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.2        | Command introduced    |
+-------------+-----------------------+