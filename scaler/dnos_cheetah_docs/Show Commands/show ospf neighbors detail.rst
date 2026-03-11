show ospf neighbors detail
--------------------------

**Minimum user role:** viewer

To display detailed information on all OSPF Neighbors:



**Command syntax: show ospf** instance [ospf-instance-name] **neighbors detail** all

**Command mode:** operational



.. **Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

	- all - include down status neighbor

**Parameter table**

+--------------------+----------------------------------------------------------------+
| Parameter          | Description                                                    |
+====================+================================================================+
| all                | Use to also display neighbors that are down                    |
+--------------------+----------------------------------------------------------------+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance. |
+--------------------+----------------------------------------------------------------+

**Example**
::

	dnRouter# show ospf neighbors detail

	Ospf Instance instance1
	Neighbor 10.170.0.66, interface address 10.170.0.66
	    In the area 0.0.0.0 via interface bundle-2.1011
	    Neighbor priority is 2, State is Full, for 2m47s, 701 state changes
	    Most recent state change statistics:
	      Progressive change 1m27s ago
	      Regressive change 1m28s ago, due to 1-WayReceived
	    DR is 0.0.0.0, BDR is 0.0.0.0
	    Options 66 *|O|-|-|-|-|E|*
	    Dead timer due in 46.774s
	    Database Summary List 0
	    Link State Request List 0
	    Link State Retransmission List 0
	    Thread Inactivity Timer on
	    Thread Database Description Retransmision off
	    Thread Link State Request Retransmission on
	    Thread Link State Update Retransmission on
	    BFD: Enabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3

	 Neighbor 10.170.1.66, interface address 10.170.1.66
	    In the area 0.0.0.0 via interface bundle-2.1012
	    Neighbor priority is 2, State is Full, for 2m47s, 1362 state changes
	    Most recent state change statistics:
	      Progressive change 1m34s ago
	      Regressive change 2m04s ago, due to 1-WayReceived
	    DR is 10.170.1.66, BDR is 10.170.1.65
	    Options 66 *|O|-|-|-|-|E|*
	    Dead timer due in 35.561s
	    Database Summary List 0
	    Link State Request List 0
	    Link State Retransmission List 0
	    Thread Inactivity Timer on
	    Thread Database Description Retransmision off
	    Thread Link State Request Retransmission on
	    Thread Link State Update Retransmission on
	    BFD: Enabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3

	 Neighbor 10.170.4.1, interface address 10.170.5.2
	    In the area 0.0.0.0 via interface bundle-2.2400
	    Neighbor priority is 1, State is Full, for 2m47s, 5 state changes
	    Most recent state change statistics:
	      Progressive change 1d00h02m ago
	    DR is 0.0.0.0, BDR is 0.0.0.0
	    Options 82 *|O|-|EA|-|-|E|*
	    Dead timer due in 37.160s
	    Database Summary List 0
	    Link State Request List 0
	    Link State Retransmission List 0
	    Thread Inactivity Timer on
	    Thread Database Description Retransmision off
	    Thread Link State Request Retransmission on
	    Thread Link State Update Retransmission on
	    BFD: Disabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3


	dnRouter# show ospf instance instance1 neighbors detail

	Ospf Instance instance1
	Neighbor 10.170.0.66, interface address 10.170.0.66
	    In the area 0.0.0.0 via interface bundle-2.1011
	    Neighbor priority is 2, State is Full, for 2m47s, 701 state changes
	    Most recent state change statistics:
	      Progressive change 1m27s ago
	      Regressive change 1m28s ago, due to 1-WayReceived
	    DR is 0.0.0.0, BDR is 0.0.0.0
	    Options 66 *|O|-|-|-|-|E|*
	    Dead timer due in 46.774s
	    Database Summary List 0
	    Link State Request List 0
	    Link State Retransmission List 0
	    Thread Inactivity Timer on
	    Thread Database Description Retransmision off
	    Thread Link State Request Retransmission on
	    Thread Link State Update Retransmission on
	    BFD: Enabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3

	 Neighbor 10.170.1.66, interface address 10.170.1.66
	    In the area 0.0.0.0 via interface bundle-2.1012
	    Neighbor priority is 2, State is Full, for 2m47s, 1362 state changes
	    Most recent state change statistics:
	      Progressive change 1m34s ago
	      Regressive change 2m04s ago, due to 1-WayReceived
	    DR is 10.170.1.66, BDR is 10.170.1.65
	    Options 66 *|O|-|-|-|-|E|*
	    Dead timer due in 35.561s
	    Database Summary List 0
	    Link State Request List 0
	    Link State Retransmission List 0
	    Thread Inactivity Timer on
	    Thread Database Description Retransmision off
	    Thread Link State Request Retransmission on
	    Thread Link State Update Retransmission on
	    BFD: Enabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3

	 Neighbor 10.170.4.1, interface address 10.170.5.2
	    In the area 0.0.0.0 via interface bundle-2.2400
	    Neighbor priority is 1, State is Full, for 2m47s, 5 state changes
	    Most recent state change statistics:
	      Progressive change 1d00h02m ago
	    DR is 0.0.0.0, BDR is 0.0.0.0
	    Options 82 *|O|-|EA|-|-|E|*
	    Dead timer due in 37.160s
	    Database Summary List 0
	    Link State Request List 0
	    Link State Retransmission List 0
	    Thread Inactivity Timer on
	    Thread Database Description Retransmision off
	    Thread Link State Request Retransmission on
	    Thread Link State Update Retransmission on
	    BFD: Disabled
        BFD min-rx: 300 min-tx: 300 multiplier: 3


	dnRouter# show ospf neighbors detail all


	dnRouter# show ospf instance instance1 neighbors detail all

.. **Help line:** Displays OSPF neighbors detailed information

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 11.6    | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 15.0    | Updated display of duration and added counter of state changes |
+---------+----------------------------------------------------------------+
| 18.2    | Added instance parameter                                       |
+---------+----------------------------------------------------------------+
