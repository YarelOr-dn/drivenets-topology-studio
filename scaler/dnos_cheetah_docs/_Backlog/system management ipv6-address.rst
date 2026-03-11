system management ipv6-address - deprecated
-------------------------------------------

**Command syntax: system management virtual-ipv6-address [virtual-ipv6-address]** vid[vid]

**Description:** configure management interface ipv6 address.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management virtual-ipv6-address 2001:1111::0/124 
	vid 24
	
	dnRouter(cfg-system)# no management ipv6-address
	
	
**Command mode:** config

**TACACS role:** operator

**Note:** "no management ipv6-address" removes IPv6 address configuration from mgmt interface.

**Help line:** configure management interface ipv6 address.

**Parameter table:**

+----------------------+-----------------------+---------------+
| Parameter            | Values                | Default value |
+======================+=======================+===============+
| virtual-ipv6-address | {ipv6-address format} |               |
+----------------------+-----------------------+---------------+
| vid                  | 0-255                 |               |
+----------------------+-----------------------+---------------+
