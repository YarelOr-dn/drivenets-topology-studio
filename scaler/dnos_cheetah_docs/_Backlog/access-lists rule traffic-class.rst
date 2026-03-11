access-lists rule traffic-class - supported in v12
--------------------------------------------------

**Command syntax: rule [rule-id] [rule-type]** traffic-class [traffic-class]

**Description:** configure access-lists protocol. Access-list type can be ipv6 only.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists 
	dnRouter(cfg-acl)# ipv6 MyAccess_list_2
	dnRouter(cfg-acl-ipv6)# rule 200 allow src-ip 2001:abcd::0/127 traffic-class 0
	dnRouter(cfg-acl-ipv6)# rule 300 deny dest-ip 2001:abcd::0/127 traffic-class 2
	
	dnRouter(cfg-acl-ipv6)# no rule 300 allow traffic-class
	
	
**Command mode:** config

**TACACS role:** operator

**Note:**

no commands remove the access-lists configuration

not supported by access-list type ipv4

not supported by egress IPv6 ACLs. When IPv6 ACL is attached as egress ACL policy (direction out) to the interface, the "protocol" parameters is referred as "any" by the system.

**Help line:** Configure access-lists rule protocol

**Parameter table:**

+---------------+------------+---------------+
| Parameter     | Values     | Default value |
+===============+============+===============+
| rule-id       | 1-65434    |               |
+---------------+------------+---------------+
| rule-type     | allow/deny |               |
+---------------+------------+---------------+
| traffic-class | 0-63       |               |
+---------------+------------+---------------+
