request interface management ipv6-address
-------------------------------------------------------------------

**Minimum user role:** operator


To configure the ipv6-address on the management bond interface:


**Command syntax: request interfaces management [interface-name] ipv6-address {[ipv6-address] \| dhcp}**

**Command mode:** GI

.. **Note:**


**Parameter table:**

+------------------+----------------------------------------------+--------+---------+
| Parameter        | Values                                       | Range  | Default |
+==================+==============================================+========+=========+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1                       |        | \-      |
+------------------+----------------------------------------------+--------+---------+
| ipv6-address     | {ipv6-address format}                        |        | \-      |
+------------------+----------------------------------------------+--------+---------+

**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 ipv6-address 2001:ab12::1/127
	dnRouter# request interfaces management mgmt-ncc-0 ipv6-address dhcp


.. **Help line:** Configure ipv6-address on management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
