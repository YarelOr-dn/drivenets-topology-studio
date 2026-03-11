access-lists rule dscp - supported in v12
-----------------------------------------

**Command syntax: rule [rule-id] [rule-type]** dscp [dscp]

**Description:** configure access-lists protocol. Access-list type can be ipv4 only.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists 
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 100 allow dscp 56
	dnRouter(cfg-acl-ipv4)# rule 101 allow src-ip 1.2.3.4/20 dscp 48
	dnRouter(cfg-acl-ipv4)# rule 102 deny dest-ip 1.1.1.1/32 dscp 32 protocol tcp src-ports 100-200
	
	dnRouter(cfg-acl-ipv4)# no rule 300 allow dscp
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

not supported for access-list type ipv6

no commands remove the access-lists configuration

**Help line:** Configure access-lists rule dscp

**Parameter table:**

+-----------+------------+---------------+
| Parameter | Values     | Default value |
+===========+============+===============+
| rule-id   | 1-65434    |               |
+-----------+------------+---------------+
| rule-type | allow/deny |               |
+-----------+------------+---------------+
| dscp      | 0-63       |               |
+-----------+------------+---------------+
