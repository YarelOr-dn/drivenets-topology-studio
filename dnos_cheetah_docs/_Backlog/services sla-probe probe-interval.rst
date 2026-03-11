services sla-probe probe-interval - N/A for this version
--------------------------------------------------------

**Command syntax: owner [owner-name] test [test-name]** probe-interval [probe-interval]

**Description:** Sets how often a probe will be issued within a test cycle

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe 
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 probe-interval 1
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest2 probe-interval 30
	
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1 probe-interval
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

probe-interval command

no commands revert the sla-probe probe-interval to its default value

**Help line:** configure sla-probe probe-interval (in seconds)

**Parameter table:**

+----------------+------------------+---------------+
| Parameter      | Values           | Default value |
+================+==================+===============+
| owner-name     | string [32 char] |               |
+----------------+------------------+---------------+
| test-name      | string [32 char] |               |
+----------------+------------------+---------------+
| probe-interval | 1-300 [seconds]  | 1             |
+----------------+------------------+---------------+
