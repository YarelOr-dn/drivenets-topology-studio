interfaces global-access-list - supported in v12
------------------------------------------------

**Command syntax: global-access-list [access-list-type] [access-list-name] direction [direction]**

**Description:** configure interface global access-list. The purpose of this access-list is to provide a common access list used by multiple interfaces in the system. This access-list can be configured on an interface in addition to "interfaces access-list". evaluation of global access-list is done before the interface specific access-list.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1
	dnRouter(cfg-if-bundle-1)# global-access-list ipv4 MyAccess-listv4 direction in

	dnRouter(cfg-if)# bundle-1.10
	dnRouter(cfg-if-bundle-1.10)# global-access-list ipv4 MyAccess-listv4 direction in

	dnRouter(cfg-if)# ge100-1/1/1
	dnRouter(cfg-if-ge100-1/1/1)# global-access-list ipv4 MyAccess-listv4 direction in


	dnRouter(cfg-if-ge100-1/1/1)# # no global-access-list
	dnRouter(cfg-if-ge100-1.20)# no global-access-list ipv4
	dnRouter(cfg-if-bundle-2)# no global-access-list ipv4 MyAccess-listv4


**Command mode:** config

**TACACS role:** operator

**Note:**

global-access-list names are filtered according to the types (ipv4/ipv6)

no command removes a specific access-list, or all access-lists in a specific type/all types

global ACL is supported for ingress ACLs only (direction in)

**Help line:** Configure interface access-list

**Parameter table:**

+------------------+---------------------------------------+---------------+
| Parameter        | Values                                | Default value |
+==================+=======================================+===============+
| interface-name   | ge<interface speed>-<A>/<B>/<C>       |               |
|                  |                                       |               |
|                  | geX-<f>/<n>/<p>.<sub-interface id>    |               |
|                  |                                       |               |
|                  | bundle-<bundle-id>                    |               |
|                  |                                       |               |
|                  | bundle-<bundle-id>.<sub-interface-id> |               |
+------------------+---------------------------------------+---------------+
| access-list-type | ipv4/ipv6                             |               |
+------------------+---------------------------------------+---------------+
| access-list-name | string                                |               |
+------------------+---------------------------------------+---------------+
| direction        | in                                    |               |
+------------------+---------------------------------------+---------------+
