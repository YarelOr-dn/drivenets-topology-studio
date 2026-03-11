show ldp discovery
------------------

**Minimum user role:** viewer

To display the status of the LDP discovery process:



**Command syntax: show ldp** [address-family] **discovery**

**Command mode:** operational



**Parameter table**

+----------------+---------------------------------------------------------------+-------+
| Parameter      | Description                                                   | Range |
+================+===============================================================+=======+
| address-family | Display LDP discovery process for the specific address-family | IPv4  |
+----------------+---------------------------------------------------------------+-------+




**Example**
::

	dnRouter# show ldp discovery
	Local LDP Identifier: 100.70.1.45:0
	Discovery Sources:
	  Interfaces:
	    bundle-2.1012: xmit/recv
	      LDP Id: 9.9.9.9:0, Transport address: 9.9.9.9
	      	  Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 20 sec], Remaining 13 sec
	    bundle-2.1011: xmit/recv
	      LDP Id: 7.7.7.7:0, Transport address: 7.7.7.7
	      	  Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 10 sec
	  Targeted Hellos:


    dnRouter# show mpls ldp discovery
	Local LDP Identifier: 1.1.1.1:0
	Discovery Sources:
	Interfaces:
		eth1: xmit/recv
		LDP Id: 2.2.2.2:0, Transport address: 2.2.2.2
			Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 12 sec
			Local Hello Interval: 5 sec
	Targeted Hellos:
		Targeted address: 4.4.4.4 xmit/recv     reason: ldp-tunneling rLFA
		LDP Id: 4.4.4.4:0, Transport address: 4.4.4.4
			Hello Holdtime: Negotiated: 45 sec, [Local: 45 sec, Remote: 45 sec], Remaining 42 sec
			Local Hello Interval: 15 sec
			Contributing tunnels: tunnel4_1, tunnel4_2, tunnel4_3, tunnel4_4, tunnel4_5, tunnel4_6, tunnel4_7, tunnel4_8, tunnel4_9
			Contributing sr-te policies: poly4_1, poly4_2, poly4_3, poly4_4, poly4_5, poly4_6, poly4_7, poly4_8, poly4_9

.. **Help line:** displays the status of the LDP discovery process

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 15.0    | Added support for the display of targeted-hellos |
+---------+--------------------------------------------------+


