set mgmt dnor-server
--------------------

**Command syntax: set mgmt dnor-server [address-list]**

**Description:** Configures DNOR servers IP/FQDN.


**CLI example:**
::

	dnRouter# set mgmt dnor-server 172.16.45.23

	dnRouter# set mgmt dnor-server 172.16.45.23,172.16.45.24,72.16.45.23

	dnRouter# set mgmt dnor-server dnor1.mydomain.com,dnor2.mydomain.com


		
**Command mode:** operational

**Note:**

-  if DHCP/DHCPv6 is enabled on the whitebox mgmt interface, whitebox may get additional DNOR address in DHCP option 66 or DHCPv6 option 59.

**Help line:** Configure DNOR servers.

**Parameter table:**

+----------------------+---------------------------------------------+---------------+
| Parameter            | Values                                      | Default value |
+======================+=============================================+===============+
| address-list         | list of up to 3 FQDNs or ipv4/ipv6          |               |
|                      |                                             |               | 
|                      | addresses, separated by comma               |               |
+----------------------+---------------------------------------------+---------------+

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
|             |                                              |
| 16.1        | Command introduced                           |
+-------------+----------------------------------------------+
| 19.1        | Added IPv6 support                           |
+-------------+----------------------------------------------+
