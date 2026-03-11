protocols rsvp auto-mesh tunnel-template igp-instance isis
----------------------------------------------------------

**Minimum user role:** operator

To configure the IGP protocol to be used by CSPF in path calculation. In the event the protocol is ISIS, the instance name must be provided:

**Command syntax: igp-instance isis [instance-name]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp tunnel

**Parameter table**

+---------------+----------------------------+------------------+---------+
| Parameter     | Description                | Range            | Default |
+===============+============================+==================+=========+
| instance-name | igp protocol instnace name | | string         | \-      |
|               |                            | | length 1-255   |         |
+---------------+----------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# igp-instance isis AREA_1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL2
    dnRouter(cfg-protocols-rsvp-tunnel)# igp-instance isis AREA_2


**Removing Configuration**

To revert to the system default behavior:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no igp-instance

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 10.0    | Command introduced                                      |
+---------+---------------------------------------------------------+
| 13.1    | Split command syntax - protocol changed to ISIS or OSPF |
+---------+---------------------------------------------------------+
