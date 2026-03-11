set mgmt dnor-server
--------------------

**Minimum user role:** viewer

To configure DNOR servers:

**Command syntax: set mgmt dnor-server [address-list]**

**Command mode:** GI

**Note**

- If DHCP/DHCPv6 is enabled on the white box mgmt interface, the white box may get an additional DNOR address in DHCP option 66 or DHCPv6 option 59.

**Example**
::

	gi# set mgmt dnor-server 172.16.45.23

	gi# set mgmt dnor-server 172.16.45.23,172.16.45.24,72.16.45.23

	gi# set mgmt dnor-server dnor1.mydomain.com,dnor2.mydomain.com


.. **Hidden Note:**

**Parameter table:**

.. **Help line:** Configure DNOR servers.

+--------------+---------------------------------------------------------------------+--------------+---------+
|   Parameter  | Description                                                         |     Range    | Default |
+==============+=====================================================================+==============+=========+
| address-list | A list of up to 3 FQDNs or IPv4 addresses, separated by whitespaces | FQDN address | /-      |
|              |                                                                     | A.B.C.D      |         |
+--------------+---------------------------------------------------------------------+--------------+---------+

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
