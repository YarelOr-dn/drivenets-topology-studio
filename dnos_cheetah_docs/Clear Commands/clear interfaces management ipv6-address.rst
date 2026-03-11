clear interface management ipv6-address
-------------------------------------------------------------------

**Minimum user role:** operator


To remove the ipv6-address from the management bond interface:


**Command syntax: clear interfaces management [interface-name] ipv6-address**

**Command mode:** operator

.. **Note:**


**Parameter table:**

+------------------+----------------------------------------------+-------+-------+
| Parameter        | Values                                       | Range | Value |
+==================+==============================================+=======+=======+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1                       |       | \-    |
+------------------+----------------------------------------------+-------+-------+


**Example:**
::

	dnRouter# clear interfaces management mgmt-ncc-0 ipv6-address
	

.. **Help line:** Remove ipv6-address address from management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
