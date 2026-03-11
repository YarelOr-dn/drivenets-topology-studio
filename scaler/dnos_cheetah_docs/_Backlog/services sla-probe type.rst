services sla-probe type - N/A for this version
----------------------------------------------

**Command syntax: owner [owner-name] test [test-name]** type [probe-type]

**Description:** Sets the probe type

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe 
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 type icmp-ping
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest2 type icmp-ping
	dnRouter(cfg-srv-sla)# owner MyOtherOwner test MyTest1 type icmp-ping
	
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1 type 
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

no commands revert the sla-probe type to its default value

**Help line:** configure sla-probe probe type

**Parameter table:**

+------------+------------------+---------------+
| Parameter  | Values           | Default value |
+============+==================+===============+
| owner-name | string [32 char] |               |
+------------+------------------+---------------+
| test-name  | string [32 char] |               |
+------------+------------------+---------------+
| probe-type | icmp-ping        | Icmp-ping     |
+------------+------------------+---------------+
