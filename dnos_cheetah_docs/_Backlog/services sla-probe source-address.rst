services sla-probe source-address - N/A for this version
--------------------------------------------------------

**Command syntax: owner [owner-name] test [test-name]** source-address [ipv4-address]

**Description:** The ping packet sent via defined ipv4 source-address for sla-probe.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe 
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 source-address 1.2.3.4
	
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1 source-address
	
**Command mode:** operational

**TACACS role:** operator

**Note:** no commands revert the sla-probe source-interface according system routing table

**Help line:** configure defined ipv4 source-address for sla-probe.

**Parameter table:**

+--------------+------------------+---------------+
| Parameter    | Values           | Default value |
+==============+==================+===============+
| owner-name   | string [32 char] |               |
+--------------+------------------+---------------+
| test-name    | string [32 char] |               |
+--------------+------------------+---------------+
| ipv4-address | A.B.C.D          |               |
+--------------+------------------+---------------+
