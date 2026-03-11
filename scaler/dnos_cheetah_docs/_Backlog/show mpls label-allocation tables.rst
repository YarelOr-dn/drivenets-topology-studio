show mpls label-allocation tables
---------------------------------

**Command syntax: show mpls label-allocation tables**

**Description:** displays mpls label allocation information

**CLI example:**
::

	dnRouter# show mpls label-allocation tables
	| Protocol   |   Allocated labels | label range     |   Maximum |   Threshold % |
	|------------+--------------------+-----------------+-----------+---------------|
	| ldp        |                  0 | 20001-69999     |     49999 |            75 |
	| rsvp       |                321 | 70001-99999     |     29999 |            75 |
	| bgp        |              10000 | 100001-799999   |    699999 |            75 |
	| bgp-vrf    |                  0 | 1040384-1048575 |      8192 |            75 |
	
	
	
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:**
