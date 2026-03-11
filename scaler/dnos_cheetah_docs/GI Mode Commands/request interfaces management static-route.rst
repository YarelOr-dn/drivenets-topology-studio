request interface management static address-family route next-hop
-------------------------------------------------------------------

**Minimum user role:** operator


To configure the static route on the physical management bond interface:


**Command syntax: request interfaces management [interface-name] static address-family [address-family] route** [ip-prefix] next-hop [gateway]**

**Command mode:** GI

.. **Note:**


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

	dnRouter# request interfaces management mgmt-ncc-0 static address-family ipv4 route 1.2.3.4/32 next-hop 4.2.3.1
	

.. **Help line:** Request adding static route on management bond


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
