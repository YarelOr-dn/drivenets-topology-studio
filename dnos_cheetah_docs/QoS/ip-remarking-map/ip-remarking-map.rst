qos ip-remarking-map
--------------------

**Minimum user role:** operator

The DSCP marking of an IP packet received or sent through an untrusted interface is remarked according to the per-hop-behavior (PHB) it is mapped to, that is, according to the qos-tag and drop-tag the packet is assigned by the qos policy set on the ingress interface.

The remarking map is a global table that specifies the DSCP remarking value for each of the possible combinations of qos-tag and drop-tag tuples.

The default remarking map maps qos-tag value to its IP precedence value. That is, it maps the qos-tag 3 bits to IP precedence 3 bits, which are the 3 most significant bits of the DSCP field, regardless of the assigned color (drop-tag).

When an IP packet received from an untrusted interface is placed on an MPLS tunnel, the imposed MPLS exp value is not inferred from the incoming untrusted DSCP value, rather is set according to the assigned qos-tag and drop-tag tuple, as defined in the mpls imposed exp column of the ip remarking-map table. The imposed mpls exp values are set by default to equal the assigned qos-tag.

The following is the default mapping:

+----------+----------+------------+-------------------+
| qos-tag  | drop-tag | dscp       | mpls imposed exp  |
+----------+----------+------------+-------------------+
| 0        | green    | default(0) | 0                 |
+----------+----------+------------+-------------------+
| 1        | green    | cs1 (8)    | 1                 |
+----------+----------+------------+-------------------+
| 2        | green    | cs2(16)    | 2                 |
+----------+----------+------------+-------------------+
| 3        | green    | cs3(24)    | 3                 |
+----------+----------+------------+-------------------+
| 4        | green    | cs4(32)    | 4                 |
+----------+----------+------------+-------------------+
| 5        | green    | cs5(40)    | 5                 |
+----------+----------+------------+-------------------+
| 6        | green    | cs6(48)    | 6                 |
+----------+----------+------------+-------------------+
| 7        | green    | cs7(56)    | 7                 |
+----------+----------+------------+-------------------+
| 0        | yellow   | default(0) | 0                 |
+----------+----------+------------+-------------------+
| 1        | yellow   | cs1 (8)    | 1                 |
+----------+----------+------------+-------------------+
| 2        | yellow   | cs2(16)    | 2                 |
+----------+----------+------------+-------------------+
| 3        | yellow   | cs3(24)    | 3                 |
+----------+----------+------------+-------------------+
| 4        | yellow   | cs4(32)    | 4                 |
+----------+----------+------------+-------------------+
| 5        | yellow   | cs5(40)    | 5                 |
+----------+----------+------------+-------------------+
| 6        | yellow   | cs6(48)    | 6                 |
+----------+----------+------------+-------------------+
| 7        | yellow   | cs7(56)    | 7                 |
+----------+----------+------------+-------------------+

To configure the QoS ip-remarking-map

**Command syntax: ip-remarking-map**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ip-remarking-map
    dnRouter(cfg-qos-ip-remark)#


**Removing Configuration**

To remove the IP remarking map
::

    dnRouter(cfg-qos)# no ip-remarking-map

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
