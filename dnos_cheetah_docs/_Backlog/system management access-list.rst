system management access-list - deprecated
------------------------------------------

**Command syntax: system management access-list [access-list-type] [access-list-name] direction [direction]**

**Description:** configure management interface access-list.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management access-list ipv4 MyAccess-listv4 direction in
	dnRouter(cfg-system)# management access-list ipv6 MyAccess-listv6 direction in
	
	dnRouter(cfg-system)# no management access-list
	dnRouter(cfg-system)# no management access-list ipv4
	dnRouter(cfg-system)# no management access-list ipv6
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

"no management access-list" removes all access-lists from the mgmt interface.

"no management access-list ipv4" removes ipv4 access-lists from the mgmt interface.

"no management access-list ipv6" removes ipv6 access-lists from the mgmt interface.

**Help line:** configure management interface access-list.

**Parameter table:**

+------------------+----------------------------------+---------------+
| Parameter        | Values                           | Default value |
+==================+==================================+===============+
| access-list-type | ipv4/ipv6                        |               |
+------------------+----------------------------------+---------------+
| access-list-name | string (any existing ACL policy) |               |
+------------------+----------------------------------+---------------+
| direction        | in                               |               |
+------------------+----------------------------------+---------------+
