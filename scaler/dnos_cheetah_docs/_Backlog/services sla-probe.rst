services sla-probe - N/A for this version
-----------------------------------------

**Command syntax: owner [owner-name] test [test-name]** target [target] \| parameters [parameter-values]

**Description:** Configure sla-probe profile. Test is done on default vrf.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 target 1.1.1.1
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest2 type icmp-ping
	dnRouter(cfg-srv-sla)# owner MyOtherOwner test MyTest1 probe-interval 1
	dnRouter(cfg-srv-sla)# owner MyOtherOwner test MyTest1 test-interval 1
	dnRouter(cfg-srv-sla)# owner MyOtherOwner test MyTest1 target 2.2.2.2
	dnRouter(cfg-srv-sla)# owner MyOtherOwner test MyTest1 history-size 512

	dnRouter(cfg-srv)# no sla-probe
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1

**Command mode:** operational

**TACACS role:** operator

**Note:**

sla-probe profile must contain owner, test & target in order for the probe test to occur.

no command removes the sla-probe profile

Total 30 tests are supported per owner

**Help line:** configure sla-probe profile

**Parameter table:**

+------------------+---------------------------------------+---------------+
| Parameter        | Values                                | Default value |
+==================+=======================================+===============+
| owner-name       | string [32 char]                      |               |
+------------------+---------------------------------------+---------------+
| test-name        | string [32 char]                      |               |
+------------------+---------------------------------------+---------------+
| target           | A.B.C.D(ipv4 host address)            |               |
+------------------+---------------------------------------+---------------+
| total-probes     | 1-15                                  | 1             |
+------------------+---------------------------------------+---------------+
| probe-type       | icmp-ping                             | Icmp-ping     |
+------------------+---------------------------------------+---------------+
| probe-interval   | 1-300 [seconds]                       | 1             |
+------------------+---------------------------------------+---------------+
| test-interval    | 0-3600 [seconds]                      | 0             |
+------------------+---------------------------------------+---------------+
| history-size     | 1-1024                                | 300           |
+------------------+---------------------------------------+---------------+
| egress-interface | ge<interface speed>-<A>/<B>/<C>       |               |
|                  |                                       |               |
|                  | geX-<f>/<n>/<p>.<sub-interface id>    |               |
|                  |                                       |               |
|                  | bundle-<bundle id>                    |               |
|                  |                                       |               |
|                  | bundle-<bundle id>.<sub-interface id> |               |
|                  |                                       |               |
|                  | lo<lo-interface id>                   |               |
+------------------+---------------------------------------+---------------+
