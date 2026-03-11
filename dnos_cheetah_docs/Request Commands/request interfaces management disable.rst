request interface management disable
-------------------------------------------------------------------

**Minimum user role:** operator


To disable the management physical or management bond interface:


**Command syntax: request interfaces management [interface-name] disable**

**Command mode:** operator

**Note:**


**Parameter table:**

+------------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter        | Values                                                                           | Range  | Default |
+==================+==================================================================================+========+=========+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1, mgmt-ncc-0/0, mgmt-ncc-0/1, mgmt-ncc-1/0, mgmt-ncc-1/1   |        | \-      |
+------------------+----------------------------------------------------------------------------------+--------+---------+


**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 disable


.. **Help line:** Disabling management physical or management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
