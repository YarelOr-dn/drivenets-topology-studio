protocols rsvp explicit-null
----------------------------

**Minimum user role:** operator

This command sets explicit-null behavior for the LSP. When enabled, the last LSR in the LSP will advertise label 0 to indicate to the penultimate router to push label 0 instead of popping the last label.

When disabled, the egress LSR advertises an implicit null label (label 3) to indicate to the penultimate router to remove (pop) the tunnel's label. When the packet arrives to the egress LSR, the egress LSR only needs to perform IP lookup, saving it from doing a label lookup first.
Although implicit-null is more efficient, explicit-null is useful for maintaining class of service (CoS). When a packet or Ethernet frame is encapsulated in MPLS, you can you can set the EXP bits independently, so that the LSP CoS is different than the payload CoS. In this case, if you use implicit-null, the LSP CoS will be lost when the penultimate LSR pops the label and the packet will be queued on the outgoing interface according to the CoS behavior of the underlying payload. With explicit-null, however, the MPLS header is preserved until the packet reaches the egress, preserving the LSP CoS behavior across the entire LSP.
To enable/disable explicit-null behavior for the LSP:

**Command syntax: explicit-null [explicit-null]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  default system behavior is implicit-null were penultimate-hop router removes the tunnel label

-  Changing the explicit-null admin-state will only affect new tunnels.

.. -  no command returns explicit-null to default value

**Parameter table**

+---------------+----------------------------------------+--------------+----------+
| Parameter     | Description                            | Range        | Default  |
+===============+========================================+==============+==========+
| explicit-null | Set explicit-null behavior for the LSP | | enabled    | disabled |
|               |                                        | | disabled   |          |
+---------------+----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# explicit-null enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp)# no explicit-null

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
