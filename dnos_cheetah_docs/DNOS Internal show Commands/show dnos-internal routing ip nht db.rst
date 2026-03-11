show dnos-internal routing ip nht db
-----------------------------------------------

**Minimum user role:** viewer

To display RIB Nexthop-OID:

**Command syntax:show dnos-internal routing ip nht db** 

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing ip nht db

	Nexthop OID-DB by OID [1378]:
	OID   Nexthop              Type                           State     Flags      DP_if  Vrf    RefCnt    FRR
	1     if 1                 Directly connected             active    0x000003   0      0      3
	2     if 9217              Directly connected             active    0x000003   8193   0      4
	3     100.70.0.254         IPv4 nexthop                   active    0x004001   13372  0      2
	4     if 65536             Directly connected             active    0x000003   0      0      1
	5     if 65539             Directly connected             active    0x000003   0      0      1
	6     if 1074              Directly connected             active    0x000003   50     0      3
	7     if 14386             Directly connected             active    0x000003   13362  0      3
	8     if 14387             Directly connected             active    0x000003   13363  0      3
	9     if 14388             Directly connected             active    0x000003   13364  0      3
	10    if 14389             Directly connected             active    0x000003   13365  0      3
	11    if 14390             Directly connected             active    0x000003   13366  0      3
	12    if 14391             Directly connected             active    0x000003   13367  0      3
	13    if 14392             Directly connected             active    0x000003   13368  0      3
	14    if 14393             Directly connected             active    0x000003   13369  0      3
	15    if 14394             Directly connected             active    0x000003   13370  0      3
	16    if 14395             Directly connected             active    0x000003   13371  0      3
	...

.. **Help line:** Displays RIB Nexthop-OID

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+


