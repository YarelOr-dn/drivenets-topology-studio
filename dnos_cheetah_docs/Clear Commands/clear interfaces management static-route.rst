clear interface management static address-family route next-hop
-------------------------------------------------------------------

**Minimum user role:** operator


To remove the static route from the physical management bond interface:


**Command syntax: clear interfaces management [interface-name] static address-family [address-family] route** [ip-prefix] next-hop [gateway]**

**Command mode:** operator

**Note:**


**Parameter table:**

+----------------+-------------------------------------------+-------+---------+
| Parameter      | Values                                    | Range | Default |
+================+===========================================+=======+=========+
| interface-name | mgmt-ncc-0, mgmt-ncc-1                    |       | \-      |
+----------------+-------------------------------------------+-------+---------+
| address-family | ipv4 / ipv6                               |       | \-      |
+----------------+-------------------------------------------+-------+---------+
| ip-prefix      | {ipv4-prefix format},{ipv6-prefix format} |       | \-      |
+----------------+-------------------------------------------+-------+---------+
| gateway        | ipv4 / ipv6 addresses                     |       | \-      |
+----------------+-------------------------------------------+-------+---------+


**Example:**
::

	dnRouter# clear interfaces management mgmt-ncc-0 static address-family ipv4 route 1.2.3.4/32 next-hop 4.2.3.1
	

.. **Help line:** Remove static route on management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
