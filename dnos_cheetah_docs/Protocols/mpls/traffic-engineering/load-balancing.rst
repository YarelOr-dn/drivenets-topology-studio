protocols mpls traffic-engineering load-balancing
-------------------------------------------------

**Minimum user role:** operator


Equal-cost multi-path routing (ECMP) allows Next-Hop packet forwarding to a single destination to occur over multiple best paths, which tie for the top place in routing metric calculations.
Weighted Equal Cost Multipath (WECMP) for Resource Reservation Protocol (RSVP), an enhancement of ECMP, allows RSVP traffic to be distributed across multiple tunnels with differing weights based on tunnel bandwidth, providing greater flexibility in load balancing and ensuring that traffic is distributed across available paths.
Enables weighted ECMP for TE tunnels forwarding. 
Each of the ECMP tunnel paths will have weight matching the tunnel bandwidth or explicit weight settings.  
Traffic will be load balanced between the different paths per the path weight ratio.

**Command syntax: load-balancing [LB-Type]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

- Reconfig of the load-balancing method will not cause traffic loss but may not be performed in the PIC manner.

**Parameter table**

+-----------+---------------------------------------------+-------------------+---------+
| Parameter | Description                                 | Range             | Default |
+===========+=============================================+===================+=========+
| LB-Type   | MPLS TE multiple path load balancing method | | ecmp            | ecmp    |
|           |                                             | | weighted-ecmp   |         |
+-----------+---------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# traffic-engineering
    dnRouter(cfg-protocols-mpls-te)# load-balancing weighted-ecmp


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-mpls-te)# no load-balancing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
