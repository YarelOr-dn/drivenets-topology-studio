clear dhcp interface
----------------------


**Minimum user role:** operator

To clear the DHCP aquired IP address for a specific interface, use the following command:

**Command syntax: clear dhcp interface [interface-name]** [ipv4-address | ipv6-address]  

**Command mode:** operation

.. **Hierarchies**

**Note**

- If no ipv4-address / ipv6-address parameters are specified, both IPv4 and IPv6 addresses are released

- If ipv4-address parameter is specified, IPv4 address is released 

- If ipv6-address parameter is specified, IPv4 address is released.

**Parameter table:**

+-------------------+--------------------------------------------------------------------------------+--------------------------------------+-------------+
|                   |                                                                                |                                      |             |
| Parameter         | Description                                                                    | Range                                | Default     |
+===================+================================================================================+======================================+=============+
|                   |                                                                                |                                      |             |
| interface-name    | The name of the interface for which you want to clear all dhcp IP addresses    | mgmt0, mgmt-ncc-0, mgmt-ncc-1        | \-          |
+-------------------+--------------------------------------------------------------------------------+--------------------------------------+-------------+


**Example**
::

	dnRouter# clear dhcp interface mgmt0
	dnRouter# clear dhcp interface mgmt-ncc-0 ipv4-address
	dnRouter# clear dhcp interface mgmt-ncc-1 ipv6-address

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+