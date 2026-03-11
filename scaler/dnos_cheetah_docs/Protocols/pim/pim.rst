protocols pim
-------------

**Minimum user role:** operator

Protocol Independent Multicast (PIM) is a collection of protocols used in a multicast environment. The main PIM protocols are: PIM Sparse Mode (PIM-SM) and PIM Dense Mode (PIM-DM). A combination of the two (PIM Sparse-Dense mode) is also sometimes used.

In PIM-SM, routers need to explicitly announce that they want to receive multicast messages from multicast groups, while PIM-DM protocols assumes that all routers want to receive multicast messages unless they state otherwise.
PIM-SM is the method used to route multicast packets from a source to multicast groups. It is used when only some of the recipients want to receive the multicast packet. In PIM-SM, a Rendezvous Point (RP) is used to receive multicast packets from the source and deliver them to the recipient.

Each domain in PIM-SM has a set of routers acting as RPs, which can be viewed as an exchange point where the source and recipients meet. First-hop routers are responsible for registering the sources to the RP and the latter is responsible for building a shortest path tree (SPT) to the source once it receives traffic from the source, thus creating a (S,G) entry between the router and the source. Last-hop routers are responsible for registering the recipients to the RP by creating a (\*,G) entry between the recipient and the RP. When a source transmits multicast data, the traffic flows to the RP and then to the recipients.

Enters the PIM configuration hierarchy level:

**Command syntax: pim**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To remove all PIM configuration:
::

    dnRouter(cfg-protocols)# no pim

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
