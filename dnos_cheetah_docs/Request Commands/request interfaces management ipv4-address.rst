request interface management ipv4-address
-------------------------------------------------------------------

**Minimum user role:** operator


To configure the ipv4-address on the management bond interface:


**Command syntax: request interfaces management [interface-name] ipv4-address {[ipv4-address] \| dhcp}**

**Command mode:** operator

.. **Note:**


**Parameter table:**

+------------------+----------------------------------------------+-------+-------+
| Parameter        | Values                                       | Range | Value |
+==================+==============================================+=======+=======+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1                       |       | \-    |
+------------------+----------------------------------------------+-------+-------+
| ipv4-address     | A.B.C.D/X                                    |       | \-    |
+------------------+----------------------------------------------+-------+-------+


**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 ipv4-address 1.2.3.4/32
	dnRouter# request interfaces management mgmt-ncc-0 ipv4-address dhcp
	

.. **Help line:** Configure ipv4-address on management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
