show dnos-internal routing rib-manager database flowspec
--------------------------------------------------------

**Minimum user role:** viewer

To display flowspec NLRIs installed in RIB:

**Command syntax: show dnos-internal routing rib-manager database flowspec**

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing rib-manager database flowspec
	IPv4 Flowspec table (total size: 1):
	-------------------------------
	DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
	    flowspec-traffic-rate:0

	IPv6 Flowspec table (total size: 1):
	-------------------------------
	DstPrefix:=aaaa::11:11:0:0/96,SrcPrefix:=bbbb::11:22:33:44/128,DstPort:<9&>6|=12,SrcPort:=50|=30,TrafficClass:=6
	    flowspec-traffic-rate:0

.. **Help line:** Displays flowspec nlris installed in RIB

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+


