access-lists maximum-rules-ingress-threshold
--------------------------------------------

**Command syntax: maximum-rules-ingress-threshold [threshold]**

**Description:** configure threshold for amount of ingress ACL entries per NCP.

Threshold per ingress ACLs specifies the utilization percentage of ingress ACL DB in the TCAM memory of NCP. When ingress ACL DB utilization in the TCAM exceeds the configured threshold, a system-event is generated notifying the user that ingress ACL TCAM is highly utilized. The threshold is percentage of maximum ingress ACL table size in TCAM. The threshold is configured per system and it is same for all NCPs.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists
	dnRouter(cfg-acl)# maximum-rules-ingress-threshold 30

	dnRouter(cfg-acl)# no maximum-rules-ingress-treshold

**Command mode:** config

**TACACS role:** operator

**Note:**

no commands revert the ingress ACL threshold to its default value

**Help line:** configure threshold for amount of ingress ACL entries per NCP.

**Parameter table:**

+-----------+-----------+---------------+
| Parameter | Values    | Default value |
+===========+===========+===============+
| threshold | 1-100 [%] | 75 [%]        |
+-----------+-----------+---------------+
