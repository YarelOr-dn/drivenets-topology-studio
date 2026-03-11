show mpls route p2mp
--------------------

**Minimum user role:** viewer

The show mpls route command displays mLDP routing and forwarding information.


**Command syntax: show mpls route p2mp** in-label [mpls-label]

**Command mode:** operational



.. **Note**


**Parameter table**

+------------+------------------------------------------+-------------+---------+
| Parameter  | Description                              | Range       | Default |
+============+==========================================+=============+=========+
| mpls-label | Filters the information by ingress label | 0..1048575  | \-      |
+------------+------------------------------------------+-------------+---------+

The following information is displayed on each route:

+----------------------+---------------------------------------------------+
| Attribute            | Description                                       |
+======================+===================================================+
| In Label             | The locally allocated ingress label               |
+----------------------+---------------------------------------------------+
| Uptime               | The amount of time that the route exists          |
+----------------------+---------------------------------------------------+
| Out Label            | The egress label used for forwarding              |
+----------------------+---------------------------------------------------+
| Forwarding Interface | The egress interface used for forwarding          |
+----------------------+---------------------------------------------------+
| Next Hop             | The next hop address used for forwarding          |
+----------------------+---------------------------------------------------+
| Forwarded Octets     | The total forwarded bytes counter for this entry  |
+----------------------+---------------------------------------------------+
| Forwarded Frames     | The total forwarded frames counter for this entry |
+----------------------+---------------------------------------------------+


**Example**
::

	dnRouter# show mpls route p2mp

	In label: 26002
		Uptime: 01:09:44
		Forwarding interfaces:
			Out label: 26010, Forwarding interface: ge100-1/0/1, Next hop: 10.0.3.10
			Out label: 26020, Forwarding interface: ge100-2/0/1, Next hop: 10.0.4.10
		Counters:
			Forwarded octets: 0, (0 bps / 0 Mbps)
			Forwarded frames: 0, (0 fps / 0 Mfps)


.. **Help line:** show mpls route p2mp

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 17.1    | Command introduced                              |
+---------+-------------------------------------------------+
