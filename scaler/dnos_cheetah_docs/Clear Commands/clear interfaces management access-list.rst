clear interface management access-list
-------------------------------------------------------------------

**Minimum user role:** operator

To remove management physical interface access-list

**Command syntax: clear interfaces management [interface-name] access-list [access-list-type] direction [direction]**

**Command mode:** operation

.. **Note:**


**Parameter table:**

+------------------+---------------------------------------+-------+---------+
| Parameter        | Values                                | Range | Default |
+==================+=======================================+=======+=========+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1                |       | \-      |
+------------------+---------------------------------------+-------+---------+
| access-list-type | ipv4/ipv6                             |       | \-      |
+------------------+---------------------------------------+-------+---------+
| direction        | in                                    |       | \-      |
+------------------+---------------------------------------+-------+---------+


**Example:**
::

	dnRouter# clear interfaces management mgmt-ncc-0 access-list ipv4 direction in
	

.. **Help line:** Clear static route on management physical

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
