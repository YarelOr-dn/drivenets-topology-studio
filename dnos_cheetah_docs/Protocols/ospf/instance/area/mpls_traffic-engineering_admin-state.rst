protocols ospf instance area mpls traffic-engineering admin-state
-----------------------------------------------------------------

**Minimum user role:** operator

OSPFv2 Traffic-Engineer (TE) provides a way of describing the traffic engineering topology (including bandwidth and administrative constraints) and distributing this information within a given OSPF area. This allows building a traffic engineering MPLS topology using RSVP-TE in OSPF areas.
To set the OSPFv2 MPLS traffic-engineering admin-state:

**Command syntax: mpls traffic-engineering admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Parameter table**

+-------------+-------------------------------------------+--------------+----------+
| Parameter   | Description                               | Range        | Default  |
+=============+===========================================+==============+==========+
| admin-state | OSPF MPLS Traffic Engineering admin state | | enabled    | disabled |
|             |                                           | | disabled   |          |
+-------------+-------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# mpls traffic-engineering admin-state enabled
    dnRouter(cfg-protocols-ospf-area)# mpls traffic-engineering admin-state disabled


**Removing Configuration**

To revert the admin-state to its default setting:
::

    dnRouter(cfg-ospf-area-mpls-te)# no mpls traffic-engineering admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
