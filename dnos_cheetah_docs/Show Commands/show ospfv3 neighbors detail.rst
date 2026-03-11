show ospfv3 neighbors detail
----------------------------

**Minimum user role:** viewer

To display detailed information on all OSPF Neighbors:



**Command syntax: show ospfv3 neighbors detail** all

**Command mode:** operational




**Parameter table**

+-----------+---------------------------------------------+
| Parameter | Description                                 |
+===========+=============================================+
| all       | Use to also display neighbors that are down |
+-----------+---------------------------------------------+

**Example**
::

	dnRouter# show ospfv3 neighbors detail

	 Neighbor 100.0.0.7, ge100-0/0/9.200
	    Area 0.0.0.0 via interface ge100-0/0/9.200 (ifindex 14549)
	    His IfIndex: 1 Link-local address: fe80::21d:1ff:fe00:1
	    State Full for a duration of 4d19:14:13, 0 state changes
	    His choice of DR/BDR 0.0.0.0/0.0.0.0, Priority 0
	    DbDesc status: Master SeqNum: 0x396e1500
	    Summary-List: 0 LSAs
	    Request-List: 0 LSAs
	    Retrans-List: 2 LSAs
	      [Router Id:0 Adv:100.0.0.7]
	      [Inter-Prefix Id:2155872256 Adv:100.0.0.7]
	    0 Pending LSAs for DbDesc in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSReq in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSUpdate in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSAck in Time 00:00:00 [thread off]
	    BFD: Enabled
	    BFD min-rx: 50 min-tx: 50 multiplier: 3

	 Neighbor 100.0.0.7, ge100-0/0/9.201
	    Area 0.0.0.0 via interface ge100-0/0/9.201 (ifindex 14550)
	    His IfIndex: 1 Link-local address: fe80::21d:1ff:fe00:2
	    State Full for a duration of 4d19:14:13, 0 state changes
	    His choice of DR/BDR 0.0.0.0/0.0.0.0, Priority 0
	    DbDesc status: Master SeqNum: 0x396e1500
	    Summary-List: 0 LSAs
	    Request-List: 0 LSAs
	    Retrans-List: 1 LSAs
	      [Router Id:0 Adv:100.0.0.7]
	    0 Pending LSAs for DbDesc in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSReq in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSUpdate in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSAck in Time 00:00:00 [thread off]
	    BFD: Enabled
	    BFD min-rx: 50 min-tx: 50 multiplier: 3

	 Neighbor 100.0.0.7, ge100-0/0/9.202
	    Area 0.0.0.0 via interface ge100-0/0/9.202 (ifindex 14551)
	    His IfIndex: 1 Link-local address: fe80::21d:1ff:fe00:3
	    State Full for a duration of 4d19:14:13, 0 state changes
	    His choice of DR/BDR 0.0.0.0/0.0.0.0, Priority 0
	    DbDesc status: Master SeqNum: 0x396e1500
	    Summary-List: 0 LSAs
	    Request-List: 0 LSAs
	    Retrans-List: 1 LSAs
	      [Router Id:0 Adv:100.0.0.7]
	    0 Pending LSAs for DbDesc in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSReq in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSUpdate in Time 00:00:00 [thread off]
	    0 Pending LSAs for LSAck in Time 00:00:00 [thread off]
	    BFD: Enabled
	    BFD min-rx: 50 min-tx: 50 multiplier: 3

	dnRouter# show ospfv3 neighbors detail all

.. **Help line:** Displays OSPFv3 neighbors detailed information

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 11.6    | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 15.0    | Updated display of duration and added counter of state changes |
+---------+----------------------------------------------------------------+


