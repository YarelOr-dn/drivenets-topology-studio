protocols ospf instance area interface ldp-sync
-----------------------------------------------

**Minimum user role:** operator

Synchronization between LDP and IGP ensures that LDP is fully established prior to forwarding traffic using the IGP path. All links along the IP shortest path, via the core network, must have operational LDP sessions between all LDP peers. When an LDP does not cover a portion of the network, services depending on MPLS forwarding will fail.
In the following cases IGP will avoid advertising the true cost of a link and will use the maximum cost, thus discouraging traffic forwarding through it:
- LDP is not configured on a link
- The LDP session is down
- The LDP Hello adjacency is down.

max-hold-time: When max-hold-time is set, the advertisement of max-metric in an IGP interface due to LDP-sync logic (lack of an LDP neighbor over interface) will be no more than the max-hold-time timer [in seconds].
               If the LDP session recovers earlier and the LDP-sync logic no longer requires max-metric to be advertised , the interface returns to the configured metric value.

To enable/disable LDP synchronization:

**Command syntax: ldp-sync [admin-state]** max-hold-time [max-hold-time]

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- No command returns the LDP-sync to its default state.

**Parameter table**

+---------------+--------------------------------------------------------------------+--------------+----------+
| Parameter     | Description                                                        | Range        | Default  |
+===============+====================================================================+==============+==========+
| admin-state   | OSPFv2 parameter relating to LDP/IGP synchronization               | | enabled    | disabled |
|               |                                                                    | | disabled   |          |
+---------------+--------------------------------------------------------------------+--------------+----------+
| max-hold-time | maximum time to hold interface at max-metric due to ldp-sync logic | 1-65535      | \-       |
+---------------+--------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# ldp-sync enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# ldp-sync enabled max-hold-time 300


**Removing Configuration**

To return the ldp-sync to its default value:
::

    dnRouter(cfg-ospf-area-if)# no ldp-sync

To disable max-hold-time:
::

    dnRouter(cfg-ospf-area-if)# no ldp-sync enabled max-hold-time

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 11.6    | Command introduced                |
+---------+-----------------------------------+
| 18.1    | Add max-hold-time optional config |
+---------+-----------------------------------+
