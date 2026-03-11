clear interface management ipv4-address
-------------------------------------------------------------------

**Minimum user role:** operator


To remove the ipv4-address from the management bond interface:


**Command syntax: clear interfaces management [interface-name] ipv4-address**

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

	dnRouter# clear interfaces management mgmt-ncc-0 ipv4-address
	

.. **Help line:** Remove ipv4-address address from management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
