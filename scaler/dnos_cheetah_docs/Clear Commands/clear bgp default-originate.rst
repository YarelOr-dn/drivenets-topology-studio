clear bgp default-originate
---------------------------

**Minimum user role:** operator

To re-evaluate the default originate policy:

**Command syntax: clear bgp** instance vrf [vrf-name] **default-originate [address-family]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table**

+-------------------+---------------------------------------------------------------------------------+-----------+-------------+
|                   |                                                                                 |           |             |
| Parameter         | Description                                                                     | Range     | Default     |
+===================+=================================================================================+===========+=============+
|                   |                                                                                 |           |             |
| vrf-name          | Clear only routes belonging to the specified VRF.                               | \-        | \ -         |
+-------------------+---------------------------------------------------------------------------------+-----------+-------------+
|                   |                                                                                 |           |             |
| address-family    | Clear only the specific address-family routes (IPv4-unicast or IPv6-unicast)    | \-        | \ -         |
+-------------------+---------------------------------------------------------------------------------+-----------+-------------+


**Example**
::

	dnRouter# clear bgp default-originate ipv4-unicast
	dnRouter# clear bgp default-originate ipv6-unicast
	dnRouter# clear bgp instance vrf A default-originate ipv4-unicast
	dnRouter# clear bgp instance vrf A default-originate ipv6-unicast

.. **Help line:**

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+