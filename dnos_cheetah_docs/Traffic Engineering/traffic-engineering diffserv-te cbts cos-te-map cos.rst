traffic-engineering diffserv-te cbts cos-te-map cos
---------------------------------------------------

**Minimum user role:** operator

You can configure the CoS to TE tunnel mapping. If there is no active TE tunnel matching the traffic CoS, traffic will be forwarded as follows:

-	Over the TE-class that forwards the lowest CoS value

-	If there is no available tunnels for this TE class, the TE-class with the next higher CoS value will be used

-	If there is no available TE-class that matches any of the CoS values, the CBTS constraint will not be applied and the traffic will be forwarded over all available tunnels equally (ECMP).

The default mapping:

+-----+----------+
| CoS | TE-class |
+=====+==========+
| 0   | 0        |
+-----+----------+
| 1   | 0        |
+-----+----------+
| 2   | 0        |
+-----+----------+
| 3   | 0        |
+-----+----------+
| 4   | 0        |
+-----+----------+
| 5   | 0        |
+-----+----------+
| 6   | 0        |
+-----+----------+
| 7   | 0        |
+-----+----------+

You can map multiple CoS values can to the same te-class, but different te-classes may not carry the same CoS value.

Fallback example:

dnRouter(cfg-te-diffserv-te-class-map)# te-class 0 class-type 0 priority 1

**dnRouter(cfg-te-diffserv-te-class-map)# te-class 1 class-type 1 priority 1**

**dnRouter(cfg-te-diffserv-te-class-map)# te-class 2 class-type 1 priority 2**

**dnRouter(cfg-te-diffserv-te-class-map)# te-class 3 class-type 0 priority 3**

dnRouter(cfg-te-diffserv-te-class-map)# te-class 4 class-type 0 priority 4

**dnRouter(cfg-te-diffserv-te-class-map)# te-class 5 class-type 0 priority 5**

dnRouter(cfg-te-diffserv-te-class-map)# te-class 6 class-type 0 priority 6

dnRouter(cfg-te-diffserv-te-class-map)# te-class 7 class-type 0 priority 7

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 0 te-class 5

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 1 te-class 3

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 2 te-class 3

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 3 te-class 3

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 4 te-class 3

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 5 te-class 3

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 6 te-class 3

dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 7 te-class 2

tunnels of te-class 1, 2, 3, 5 exist at first

if there are no available tunnel of TE-class 3, forward cos 1-6 to te-class 5

if also there are no available tunnel of TE-class 5, forward cos 0 & 1-6 to te-class 2

if also there are no available tunnel of TE-class 2, forward cos 0 & 1-6 & 7 to te-class 1

To configure the CoS to TE tunnel mapping:


**Command syntax: cos [cos-id] te-class [te-id]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te

**Parameter table**

+---------------+--------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                                                                      |           |             |
| Parameter     | Description                                                                                                                          | Range     | Default     |
+===============+======================================================================================================================================+===========+=============+
|               |                                                                                                                                      |           |             |
| cos-id        |  The class-of-service identifier.                                                                                                    | 0..7      | \-          |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                                                                      |           |             |
| te-id         | The identifier for a paired class-type and tunnel   priority (see "mpls traffic-engineering diffserv-te te-class-map   te-class")    | 0..7      | \-          |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**

In this example, if there is no available TE-class 3 tunnel, CoS 1-6 traffic will be directed to TE-class 5.

If there is no available TE-class 5 tunnel, CoS 0 and CoS 1-6 traffic will be directed to TE-class 2.

If TE-class 2 tunnels are also unavailable, all CoS traffic (0, 1-6, and 7) will be directed to TE-class 1.

::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# cbts
	dnRouter(cfg-te-diffserv-cbts)# cos-te-map
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 0 te-class 0
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 1 te-class 1
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 2 te-class 1
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 3 te-class 1
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 4 te-class 4
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 5 te-class 4
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 6 te-class 6
	dnRouter(cfg-diffserv-cbts-cos-te-map)# cos 7 te-class 7

**Removing Configuration**

To revert to the default mapping for a specific CoS ID:
::

	dnRouter(cfg-diffserv-cbts-cos-te-map)# no cos 3


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+