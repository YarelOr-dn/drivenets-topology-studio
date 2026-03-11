access-lists maximum-rules-egress-threshold
-------------------------------------------

**Command syntax: maximum-rules-egress-threshold [threshold]**

**Description:** configure threshold for amount of egress ACL entries per NCP.

Threshold per egress ACLs specifies the utilization percentage of egress ACL DB in the TCAM memory of NCP. When egress ACL DB utilization in the TCAM exceeds the configured threshold, a system-event is generated notifying the user that egress ACL TCAM is highly utilized. The threshold is percentage of maximum egress ACL table size in TCAM. The threshold is configured per system and it is same for all NCPs.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# maximum-rules-egress-threshold 30

	dnRouter(cfg-acl)# no maximum-rules-egress-treshold

**Command mode:** config

**TACACS role:** operator

**Note:**

no commands revert the egress ACL threshold to its default value

**Help line:** configure threshold for amount of egress ACL entries per NCP.

**Parameter table:**

+-----------+-----------+---------------+
| Parameter | Values    | Default value |
+===========+===========+===============+
| threshold | 1-100 [%] | 75 [%]        |
+-----------+-----------+---------------+
