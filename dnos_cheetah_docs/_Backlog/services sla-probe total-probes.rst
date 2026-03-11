services sla-probe total-probes - N/A for this version
------------------------------------------------------

**Command syntax: owner [owner-name] test [test-name]** total-probes [total-probes]

**Description:** Sets the total number of probes to use in a test cycle

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe 
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 total-probes 1
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest2 total-probes 10
	
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1 total-probes
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

no commands revert the sla-probe total-probes to its default value

**Help line:** configure sla-probe total-probes

**Parameter table:**

+--------------+------------------+---------------+
| Parameter    | Values           | Default value |
+==============+==================+===============+
| owner-name   | string [32 char] |               |
+--------------+------------------+---------------+
| test-name    | string [32 char] |               |
+--------------+------------------+---------------+
| total-probes | 1-15             | 1             |
+--------------+------------------+---------------+
