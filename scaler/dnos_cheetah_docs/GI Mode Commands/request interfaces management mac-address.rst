request interface management mac-address
-------------------------------------------------------------------

**Minimum user role:** operator


To configure the mac-address on the management bond interface:


**Command syntax: request interfaces management [interface-name] mac-address [mac-address]**

**Command mode:** GI

.. **Note:**


**Parameter table:**

+------------------+----------------------------------------------+--------+---------+
| Parameter        | Values                                       | Range  | Default |
+==================+==============================================+========+=========+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1                       |        | \-      |
+------------------+----------------------------------------------+--------+---------+
| mac-address      | xx:xx:xx:xx:xx:xx                            |        | \-      |
+------------------+----------------------------------------------+--------+---------+


**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 mac-address 10:22:33:44:55:00
	

.. **Help line:** Configure mac-address on management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
