system management ipv4-address - deprecated
-------------------------------------------

**Command syntax: system management virtual-ipv4-address [virtual-ipv4-address] vid[vid]**

**Description:** configure management interface ipv4 address.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management virtual-ipv4-address 10.1.1.1/24 vid 24
	
	dnRouter(cfg-system)# no management ipv4-address
	
	
**Command mode:** config

**TACACS role:** operator

**Note:** "no management ipv4-address" removes IPv4 address configuration from mgmt interface.

**Help line:** configure management interface ipv4 address.

**Parameter table:**

+----------------------+-----------------------+---------------+
| Parameter            | Values                | Default value |
+======================+=======================+===============+
| virtual-ipv4-address | {ipv4-address format} |               |
+----------------------+-----------------------+---------------+
| vid                  | 0-255                 |               |
+----------------------+-----------------------+---------------+
