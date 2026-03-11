show services sla-probe summary - N/A for this version
------------------------------------------------------

**Command syntax: show services sla-probe summary** owner [owner] test [test]

**Description:** display sla-probe summary

**CLI example:**
::

	dnRouter# show services sla-probe summary
	
	| Owner     | Test      | Target    | Total Probes | Probe Type | Probe Interval | Test Interval | History Size  | source-address   |
	|-----------+-----------+-----------+--------------+------------+----------------+---------------+---------------+-------------------|
	| MyOwner1  | MyTest1   | 1.1.1.1   | 1            | icmp-ping  | 1              | 0             | 300           |                   |
	| MyOwner2  | MyTest1   | 1.2.3.4   | 10           | icmp-ping  | 10             | 300           | 300           | 5.5.5.5           |
	| MyOwner2  | MyTest2   | 15.12.1.3 | 7            | icmp-ping  | 7              | 1             | 300           | 5.5.5.5           |
	
	dnRouter# show services sla-probe summary owner MyOwner2
	
	| Owner     | Test      | Target    | Total Probes | Probe Type | Probe Interval | Test Interval | History Size  | source-address   |
	|-----------+-----------+-----------+--------------+------------+----------------+---------------|---------------+-------------------|
	| MyOwner2  | MyTest1   | 1.2.3.4   | 10           | icmp-ping  | 10             | 300           | 300           | 5.5.5.5           |
	| MyOwner2  | MyTest2   | 15.12.1.3 | 7            | icmp-ping  | 7              | 1             | 300           |                   |
	
	dnRouter# show services sla-probe summary owner MyOwner2 test MyTest1
	
	| Owner     | Test      | Target    | Total Probes | Probe Type | Probe Interval | Test Interval | History Size  | source-address   |
	|-----------+-----------+-----------+--------------+------------+----------------+---------------|---------------+-------------------|
	| MyOwner2  | MyTest1   | 1.2.3.4   | 10           | icmp-ping  | 10             | 300           | 300           | 5.5.5.5           |
		
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** show sla-probe summary

**Parameter table:**

+----------------+----------------------------+---------------+
| Parameter      | Values                     | Default value |
+================+============================+===============+
| owner-name     | string [32 char]           |               |
+----------------+----------------------------+---------------+
| test-name      | string [32 char]           |               |
+----------------+----------------------------+---------------+
| target         | A.B.C.D(ipv4 host address) |               |
+----------------+----------------------------+---------------+
| total-probes   | 1-15                       | 1             |
+----------------+----------------------------+---------------+
| probe-type     | icmp-ping                  | Icmp-ping     |
+----------------+----------------------------+---------------+
| probe-interval | 1-300 [seconds]            | 1             |
+----------------+----------------------------+---------------+
| test-interval  | 0-3600 [seconds]           | 0             |
+----------------+----------------------------+---------------+
| history-size   | 1-1024                     | 300           |
+----------------+----------------------------+---------------+
| ipv4-address   | A.B.C.D                    |               |
+----------------+----------------------------+---------------+
