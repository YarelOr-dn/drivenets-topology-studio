interfaces qos ip-marking
-------------------------

**Minimum user role:** operator

The qos ip-marking configuration allows to determine whether the IP DSCP marking is trusted or not. If the marking is untrusted, the DSCP field is remarked on ingress and on egress. When qos ip-marking is untrusted, the DSCP field is remarked (modified) for IPv4 packets sent and received through the interface (IPv6 TC field is remarked according to the same rules). The incoming DSCP values are remarked according to the qos remarking-map table and the qos-tag and drop-tag assigned to the packet by the ingress policy rules. The DSCP can be overridden by a specific set of dscp commands on the egress policy assigned to the interface.

If qos ip-marking is trusted, the incoming packet DSCP marking is trusted, and the DSCP field is not remarked (unless sent through an untrusted interface).
MPLS packets are not expected to be sent or received through an ip-marking untrusted interface.

To designate interface QoS ip marking as trusted or untrusted:

**Command syntax: qos ip-marking [trust-mode]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

- While ip-marking is configured on physical and bundle interfaces, it applies to all IPv4 and IPv6 of their sub-interfaces.

- xconnect sub-interfaces are always trusted.

**Parameter table**

+------------+-------------------------------------------------------------+---------------+---------+
| Parameter  | Description                                                 | Range         | Default |
+============+=============================================================+===============+=========+
| trust-mode | Designate interface QoS ip marking as trusted or untrusted. | | trusted     | \-      |
|            |                                                             | | untrusted   |         |
+------------+-------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# qos ip-marking untrusted
    dnRouter(cfg-if-ge100-0/0/0)# qos ip-marking trusted


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-0/0/0)# no qos ip-marking

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
