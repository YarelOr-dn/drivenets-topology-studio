protocols ospf instance area interface bfd rsvp-dependency
----------------------------------------------------------

**Minimum user role:** operator

In the event of a failure of BFD protecting an OSPF adjacency over an interface with RSVP enabled, RSVP will consider the interface as down and will trigger a bypass of the interface. The FIB will also react and will perform Fast Re-Routing (FRR) for all tunnels using that egress interface.
To enable RSVP dependency on an interface:

**Command syntax: rsvp-dependency [rsvp-dependency]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface bfd

**Note**
- 'no' command returns to default settings

**Parameter table**

+-----------------+-----------------------------------------------------------------+--------------+---------+
| Parameter       | Description                                                     | Range        | Default |
+=================+=================================================================+==============+=========+
| rsvp-dependency | Set that BFD for OSPF interface will trigger RSVP-TE FRR events | | enabled    | \-      |
|                 |                                                                 | | disabled   |         |
+-----------------+-----------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# bfd
    dnRouter(cfg-ospf-area-if-bfd)# rsvp-dependency enabled


**Removing Configuration**

To return the rsvp dependency admin-state to its default value: 
::

    dnRouter(cfg-ospf-area-if-bfd)# no rsvp-dependency

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
