services sla-probe test-interval - N/A for this version
-------------------------------------------------------

**Command syntax: owner [owner-name] test [test-name]** test-interval [probe-interval]

**Description:** Sets the time to delay between the end of this test cycle and the start of a new cycle. A cycle ends when all probes in a test have done a probe to the target

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe 
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 test-interval 1
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest2 test-interval 30
	
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1 test-interval
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

no commands revert the sla-probe test-interval to its default value

**Help line:** configure sla-probe test-interval (in seconds)

**Parameter table:**

+---------------+------------------+---------------+
| Parameter     | Values           | Default value |
+===============+==================+===============+
| owner-name    | string [32 char] |               |
+---------------+------------------+---------------+
| test-name     | string [32 char] |               |
+---------------+------------------+---------------+
| test-interval | 0-3600 [seconds] | 0             |
+---------------+------------------+---------------+
