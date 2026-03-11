# DNOS QoS Configuration Reference

This document contains the complete DNOS CLI QoS configuration syntax from the official DriveNets documentation.

---

## deep-buffering
```rst
qos deep-buffering
------------------

**Minimum user role:** operator

To configure deep-buffering:

**Command syntax: deep-buffering [deep-buffering]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+----------------+----------------------------------+----------------+---------+
| Parameter      | Description                      | Range          | Default |
+================+==================================+================+=========+
| deep-buffering | Control deep buffering behavior. | | normal       | normal  |
|                |                                  | | hbm-bypass   |         |
+----------------+----------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# deep-buffering normal


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-qos)# no deep-buffering

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## ecn-profile
```rst
qos ecn-profile
---------------

**Minimum user role:** operator

The purpose of the Explicit Congestion Notification (ECN) is to mark packets going through a congested path.
When used, ECN signals the sender to slow the transmittion rate.
The packet marking probability is based on a minimum threshold, a maximum threshold and a linear curve that starts at a 0 drop probability and ends at max-drop-probability.
To allow small bursts with no marking, the minimum and maximum thresholds relate to the average queue size and not to the current queue size.

**Command syntax: ecn-profile [ecn-profile]**

**Command mode:** config

**Hierarchies**

- qos

**Note**

- You cannot remove a profile if it is part of qos policy that is attached to an interface.

**Parameter table**

+-------------+-----------------------------------------------+------------------+---------+
| Parameter   | Description                                   | Range            | Default |
+=============+===============================================+==================+=========+
| ecn-profile | References the configured name of the profile | | string         | \-      |
|             |                                               | | length 1-255   |         |
+-------------+-----------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1


**Removing Configuration**

To remove the ECN profile:
::

    dnRouter(cfg-qos)# no ecn-profile MyEcnProfile1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## max-probability
```rst
qos ecn-profile max-probability
-------------------------------

**Minimum user role:** operator

To configure the ECN profile max-probability which is the maximum marking probability for the profile curve:

**Command syntax: max-probability [max-probability]**

**Command mode:** config

**Hierarchies**

- qos ecn-profile

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                      | Range | Default |
+=================+==================================================================================+=======+=========+
| max-probability | marking percentage at the max of the curve. The marking probability curve starts | 1-100 | 100     |
|                 | at 0 marking at min and reaches this marking probability at the max of the       |       |         |
|                 | curve. Beyond max, the marking probability jumps to 100%.                        |       |         |
+-----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1
    dnRouter(cfg-qos-MyEcnProfile1)# max-probability 50


**Removing Configuration**

To remove the max probability:
::

    dnRouter(cfg-qos-MyEcnProfile1)# no max-probability

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## max-threshold
```rst
qos ecn-profile max-threshold
-----------------------------

**Minimum user role:** operator

To configure the ECN profile max-threshold which is the upper value for the range of the curve, above which all packets will be marked:

**Command syntax: max-threshold [max-threshold-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos ecn-profile

**Note**

- The ECN profile must be configured with both a min-threshold and max-threshold.

- The min-value must be less or equal to the max-value.

**Parameter table**

+----------------------------+-----------------------------------------------+------------------+--------------+
| Parameter                  | Description                                   | Range            | Default      |
+============================+===============================================+==================+==============+
| max-threshold-microseconds | Queue maximum drop threshold in microseconds. | 1-200000         | \-           |
+----------------------------+-----------------------------------------------+------------------+--------------+
| units                      |                                               | | microseconds   | microseconds |
|                            |                                               | | milliseconds   |              |
+----------------------------+-----------------------------------------------+------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1
    dnRouter(cfg-qos-MyEcnProfile1)# max-threshold 10000 microseconds


**Removing Configuration**

To remove the max threshold:
::

    dnRouter(cfg-qos-MyEcnProfile1)# no max-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## min-threshold
```rst
qos ecn-profile min-threshold
-----------------------------

**Minimum user role:** operator

To configure the ECN profile min-threshold which is the lower value for the range of the curve, below which no packets will be marked:

**Command syntax: min-threshold [min-threshold-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos ecn-profile

**Note**

- The ECN profile must be configured with a min-threshold and a max-threshold.

- The min-value must be less or equal to the max-value.

**Parameter table**

+----------------------------+-----------------------------------------------+------------------+--------------+
| Parameter                  | Description                                   | Range            | Default      |
+============================+===============================================+==================+==============+
| min-threshold-microseconds | Queue minimum drop threshold in microseconds. | 1-200000         | \-           |
+----------------------------+-----------------------------------------------+------------------+--------------+
| units                      |                                               | | microseconds   | microseconds |
|                            |                                               | | milliseconds   |              |
+----------------------------+-----------------------------------------------+------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1
    dnRouter(cfg-qos-MyEcnProfile1)# min-threshold 10000 microseconds


**Removing Configuration**

To remove the min threshold:
::

    dnRouter(cfg-qos-MyEcnProfile1)# no min-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## fabric-multicast
```rst
qos fabric-multicast
--------------------

**Minimum user role:** operator

DNOS supports two types of multicast replication schemes: Ingress replication and Fabric replication.

With ingress replication, multicast traffic is replicated at the ingress NCP and placed on the Virtual Output Queues (VoQs) towards the outgoing egress ports, queued together with unicast traffic sent to those egress ports. Traffic is then sent across the fabric, and then through the egress interfaces, scheduled by the end-to-end scheduler, which ensures that traffic is sent only when there are enough resources within the fabric and egress NCP.

With the fabric replication scheme, multicast traffic that needs to be sent to at least one outgoing interface in a remote NCP (i.e., traffic that needs to be sent across the fabric), is not replicated by the ingress NCP. Rather these multicast packets are placed in a Fabric-Multicast-Queue (FMQ) and replicated by the fabric to all NCPs. Each NCP recycles the multicast traffic and then replicates traffic to its local egress ports within the Outgoing Interface List (OIL) and is then placed on the egress NCP’s VoQs, together with unicast traffic. The end-to-end scheduler then schedules these packets to be sent. Multicast traffic replicated on the fabric is unscheduled, i.e. no resources are pre-allocated for this traffic on the fabric or egress NCP.

Fabric-multicast QoS adds two shapers, the ncp-to-fab shaper and the fab-to-ncp shaper. The first, ncp-to-fab shaper, ensures that the rate of unscheduled multicast traffic sent by each NCP core onto the fabric is limited to the shaper rate. The second, fab-to-ncp shaper, ensures that the maximum rate of traffic sent from the fabric to each NCP through the recycle interface is limited to the shaper rate. It protects against aggregate multicast traffic competing or overwhelming incoming traffic on the egress NCP.

For example, in a small cluster containing 4 NCPs, each NCP has two cores. The ncp-to-fab shaper is set to limit the rate to 2.5Gbps. Each NCP can place up to 5Gbps of unscheduled multicast traffic onto the fabric, replicated to each of the outgoing NCPs, i.e. a max total of 20Gbps of traffic placed by all NCPs onto the fabric. Each packet is replicated to all NCPs, delivering a total of 80Gbps of unscheduled traffic on the fabric. Each NCP will receive up to 20Gbps of multicast traffic. If the fab-to-ncp shaper is set to 10Gbps, it ensures that no more than 10Gbps of multicast traffic will be recycled to each NCP. Multicast traffic that does not have OIL members in the NCP will not be recycled to the NCP, hence the fab-to-ncp shaper will only shape traffic destined to the NCP.

**Command syntax: fabric-multicast**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# fabric-multicast
    dnRouter(cfg-qos-fab-mcast)#


**Removing Configuration**

To revert the fabric-multicast parameters to the default:
::

    dnRouter(cfg-qos)# no fabric-multicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## fab-to-ncp max-bandwidth
```rst
qos fabric-multicast fab-to-ncp max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The fab-to-ncp shaper ensures that the maximum rate of multicast traffic sent from the fabric to each NCP, through the recycle interface, is limited to the shaper rate. The limit protects against aggregate multicast traffic overwhelming or competing with incoming traffic on the egress NCP.

To configure the rate of the fabric multicast traffic:

**Command syntax: fab-to-ncp max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos fabric-multicast

**Note**

- The recycle port interface and calendar shaper are always set to 120 Gbps.

**Parameter table**

+---------------------+------------------------------------------------+-----------+---------+
| Parameter           | Description                                    | Range     | Default |
+=====================+================================================+===========+=========+
| max-bandwidth-mbits | Per core fabric multicast shaper rate in mbits | 50-100000 | 20000   |
+---------------------+------------------------------------------------+-----------+---------+
| units               |                                                | | mbps    | mbps    |
|                     |                                                | | gbps    |         |
+---------------------+------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# fabric-multicast
    dnRouter(cfg-qos-fab-mcast)# fab-to-ncp max-bandwidth 10 Gbps


**Removing Configuration**

To revert the configured rate to the default:
::

    dnRouter(cfg-qos)# no fabric-multicast fab-to-ncp max-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## ncp-to-fab max-bandwidth
```rst
qos fabric-multicast ncp-to-fab max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The ncp-to-fab shaper ensures that the rate of unscheduled multicast traffic sent by each NCP core to the fabric is limited to the shaper rate.

To configure the rate of unscheduled multicast traffic:

**Command syntax: ncp-to-fab max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos fabric-multicast

**Parameter table**

+---------------------+------------------------------------------------+-----------+---------+
| Parameter           | Description                                    | Range     | Default |
+=====================+================================================+===========+=========+
| max-bandwidth-mbits | Per core fabric multicast shaper rate in mbits | 50-100000 | 20000   |
+---------------------+------------------------------------------------+-----------+---------+
| units               |                                                | | mbps    | mbps    |
|                     |                                                | | gbps    |         |
+---------------------+------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# fabric-multicast
    dnRouter(cfg-qos-fab-mcast)# ncp-to-fab max-bandwidth 10 Gbps


**Removing Configuration**

To revert the configured rate to the default:
::

    dnRouter(cfg-qos)# no fabric-multicast ncp-to-fab max-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## hw-mapping
```rst
qos hw-mapping
--------------

**Minimum user role:** operator

To configure rules for mapping QoS policy to hardware settings:


**Command syntax: hw-mapping**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# hw-mapping
    dnRouter(cfg-qos-hw-map)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qos)# no hw-mapping

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## dscp-ipv4
```rst
qos ip-remarking-map qos-tag drop-tag dscp-ipv4
-----------------------------------------------

**Minimum user role:** operator

To configure an entry in the qos ip-remarking map:

**Command syntax: qos-tag [qos-tag] drop-tag [drop-tag] dscp-ipv4 [dscp-ipv4]** mpls-imposed-exp [mpls-imposed-exp] imposed-ipp [imposed-ipp]

**Command mode:** config

**Hierarchies**

- qos ip-remarking-map

**Note**

- Cannot configure imposed-ipp and mpls-imposed-exp with different non-default values for the same qos-tag and drop-tag pair.

**Parameter table**

+------------------+----------------------------------------------------+------------+---------+
| Parameter        | Description                                        | Range      | Default |
+==================+====================================================+============+=========+
| qos-tag          | qos-tag identifier.                                | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+
| drop-tag         | drop-tag identifier.                               | | green    | \-      |
|                  |                                                    | | yellow   |         |
+------------------+----------------------------------------------------+------------+---------+
| dscp-ipv4        | the dscp remark value for ipv4 address family.     | 0-63       | \-      |
+------------------+----------------------------------------------------+------------+---------+
| mpls-imposed-exp | the imposed mpls-exp carrying IP remarked traffic. | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+
| imposed-ipp      | the imposed ipp used for ip tunnels.               | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ip-remarking-map
    dnRouter(cfg-qos-ip-remark)#
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag green dscp-ipv4 af11
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv4 af12
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv4 af12 mpls-imposed-exp 3
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv4 af12 mpls-imposed-exp 3 imposed-ipp 3


**Removing Configuration**

To remove the qos ip-remarking-map entry:
::

    dnRouter(cfg-qos-ip-remark)# no qos-tag 4 drop-tag green

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 17.0    | Command introduced                           |
+---------+----------------------------------------------+
| 19.3    | Adding support for imposed-ipp configuration |
+---------+----------------------------------------------+
```

## dscp-ipv6
```rst
qos ip-remarking-map qos-tag drop-tag dscp-ipv6
-----------------------------------------------

**Minimum user role:** operator

To configure an entry in the qos ip-remarking map:

**Command syntax: qos-tag [qos-tag] drop-tag [drop-tag] dscp-ipv6 [dscp-ipv6]** mpls-imposed-exp [mpls-imposed-exp] imposed-ipp [imposed-ipp]

**Command mode:** config

**Hierarchies**

- qos ip-remarking-map

**Note**

- Cannot configure imposed-ipp and mpls-imposed-exp with different non-default values for the same qos-tag and drop-tag pair.

**Parameter table**

+------------------+----------------------------------------------------+------------+---------+
| Parameter        | Description                                        | Range      | Default |
+==================+====================================================+============+=========+
| qos-tag          | qos-tag identifier.                                | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+
| drop-tag         | drop-tag identifier.                               | | green    | \-      |
|                  |                                                    | | yellow   |         |
+------------------+----------------------------------------------------+------------+---------+
| dscp-ipv6        | the dscp remark value for ipv6 address family.     | 0-63       | \-      |
+------------------+----------------------------------------------------+------------+---------+
| mpls-imposed-exp | the imposed mpls-exp carrying IP remarked traffic. | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+
| imposed-ipp      | the imposed ipp used for ip tunnels.               | 0-7        | \-      |
+------------------+----------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ip-remarking-map
    dnRouter(cfg-qos-ip-remark)#
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag green dscp-ipv6 af11
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv6 af12
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv6 af12 mpls-imposed-exp 3
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp-ipv6 af12 mpls-imposed-exp 3 imposed-ipp 3


**Removing Configuration**

To remove the qos ip-remarking-map entry:
::

    dnRouter(cfg-qos-ip-remark)# no qos-tag 4 drop-tag green

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 17.0    | Command introduced                           |
+---------+----------------------------------------------+
| 19.3    | Adding support for imposed-ipp configuration |
+---------+----------------------------------------------+
```

## dscp
```rst
qos ip-remarking-map qos-tag drop-tag dscp
------------------------------------------

**Minimum user role:** operator

To configure an entry in the qos ip-remarking map:

**Command syntax: qos-tag [qos-tag] drop-tag [drop-tag] dscp [dscp]** mpls-imposed-exp [mpls-imposed-exp] imposed-ipp [imposed-ipp]

**Command mode:** config

**Hierarchies**

- qos ip-remarking-map

**Note**

- Cannot configure imposed-ipp and mpls-imposed-exp with different non-default values for the same qos-tag and drop-tag pair.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter        | Description                                                                      | Range      | Default |
+==================+==================================================================================+============+=========+
| qos-tag          | qos-tag identifier.                                                              | 0-7        | \-      |
+------------------+----------------------------------------------------------------------------------+------------+---------+
| drop-tag         | drop-tag identifier.                                                             | | green    | \-      |
|                  |                                                                                  | | yellow   |         |
+------------------+----------------------------------------------------------------------------------+------------+---------+
| dscp             | the dscp remark value for ipv4 address family. the dscp remark value for ipv6    | 0-63       | \-      |
|                  | address family.                                                                  |            |         |
+------------------+----------------------------------------------------------------------------------+------------+---------+
| mpls-imposed-exp | the imposed mpls-exp carrying IP remarked traffic.                               | 0-7        | \-      |
+------------------+----------------------------------------------------------------------------------+------------+---------+
| imposed-ipp      | the imposed ipp used for ip tunnels.                                             | 0-7        | \-      |
+------------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ip-remarking-map
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag green dscp ef
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag all dscp default
    dnRouter(cfg-qos-ip-remark)# qos-tag 4 drop-tag yellow dscp af12 mpls-imposed-exp 3


**Removing Configuration**

To remove the qos ip-remarking-map entry:
::

    dnRouter(cfg-qos-ip-remark)# no qos-tag 4 drop-tag green

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 11.2    | Command introduced                           |
+---------+----------------------------------------------+
| 19.3    | Adding support for imposed-ipp configuration |
+---------+----------------------------------------------+
```

## ip-remarking-map
```rst
qos ip-remarking-map
--------------------

**Minimum user role:** operator

The DSCP marking of an IP packet received or sent through an untrusted interface is remarked according to the per-hop-behavior (PHB) it is mapped to, that is, according to the qos-tag and drop-tag the packet is assigned by the qos policy set on the ingress interface.

The remarking map is a global table that specifies the DSCP remarking value for each of the possible combinations of qos-tag and drop-tag tuples.

The default remarking map maps qos-tag value to its IP precedence value. That is, it maps the qos-tag 3 bits to IP precedence 3 bits, which are the 3 most significant bits of the DSCP field, regardless of the assigned color (drop-tag).

When an IP packet received from an untrusted interface is placed on an MPLS tunnel, the imposed MPLS exp value is not inferred from the incoming untrusted DSCP value, rather is set according to the assigned qos-tag and drop-tag tuple, as defined in the mpls imposed exp column of the ip remarking-map table. The imposed mpls exp values are set by default to equal the assigned qos-tag.

The following is the default mapping:

+----------+----------+------------+-------------------+-------------+
| qos-tag  | drop-tag | dscp       | mpls imposed exp  | imposed ipp |
+----------+----------+------------+-------------------+-------------+
| 0        | green    | default(0) | 0                 | 0           |
+----------+----------+------------+-------------------+-------------+
| 1        | green    | cs1 (8)    | 1                 | 1           |
+----------+----------+------------+-------------------+-------------+
| 2        | green    | cs2(16)    | 2                 | 2           |
+----------+----------+------------+-------------------+-------------+
| 3        | green    | cs3(24)    | 3                 | 3           |
+----------+----------+------------+-------------------+-------------+
| 4        | green    | cs4(32)    | 4                 | 4           |
+----------+----------+------------+-------------------+-------------+
| 5        | green    | cs5(40)    | 5                 | 5           |
+----------+----------+------------+-------------------+-------------+
| 6        | green    | cs6(48)    | 6                 | 6           |
+----------+----------+------------+-------------------+-------------+
| 7        | green    | cs7(56)    | 7                 | 7           |
+----------+----------+------------+-------------------+-------------+
| 0        | yellow   | default(0) | 0                 | 0           |
+----------+----------+------------+-------------------+-------------+
| 1        | yellow   | cs1 (8)    | 1                 | 1           |
+----------+----------+------------+-------------------+-------------+
| 2        | yellow   | cs2(16)    | 2                 | 2           |
+----------+----------+------------+-------------------+-------------+
| 3        | yellow   | cs3(24)    | 3                 | 3           |
+----------+----------+------------+-------------------+-------------+
| 4        | yellow   | cs4(32)    | 4                 | 4           |
+----------+----------+------------+-------------------+-------------+
| 5        | yellow   | cs5(40)    | 5                 | 5           |
+----------+----------+------------+-------------------+-------------+
| 6        | yellow   | cs6(48)    | 6                 | 6           |
+----------+----------+------------+-------------------+-------------+
| 7        | yellow   | cs7(56)    | 7                 | 7           |
+----------+----------+------------+-------------------+-------------+

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

To revert to the default ip-remarking-map:
::

    dnRouter(cfg-qos)# no ip-remarking-map

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.2    | Command introduced |
+---------+--------------------+
```

## low-rate-shaping
```rst
qos low-rate-shaping
--------------------

**Minimum user role:** operator

To enable low rate shaping. Enabling low rate shaping allows to set for a sub interface queue rate less than a threshold. The threshold is either 2.6 Mbps ot 3.7 Mbps depands on the device frecuency 1 GHz or 1.4 GHz. Enabling low rate shaping reduces the number of supported sub-interfaces. 

**Command syntax: low-rate-shaping [low-rate-shaping]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+------------------+--------------------------+--------------+----------+
| Parameter        | Description              | Range        | Default  |
+==================+==========================+==============+==========+
| low-rate-shaping | Enable Low rate shaping. | | enabled    | disabled |
|                  |                          | | disabled   |          |
+------------------+--------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# low-rate-shaping enabled


**Removing Configuration**

To disable low-rate-shaping:
::

    dnRouter(cfg-qos)# no low-rate-shaping

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## description
```rst
qos policy description
----------------------

**Minimum user role:** operator

To add a meaningful description for a policy:

**Command syntax: description [descr]**

**Command mode:** config

**Hierarchies**

- qos policy

**Parameter table**

+-----------+--------------------+------------------+---------+
| Parameter | Description        | Range            | Default |
+===========+====================+==================+=========+
| descr     | Policy description | | string         | \-      |
|           |                    | | length 1-255   |         |
+-----------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-policy-MyQoSPOlicy1)# description "Ingress peer 1 policy"


**Removing Configuration**

To remove the description from the policy
::

    dnRouter(cfg-policy-MyQoSPOlicy1)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
```

## policy
```rst
qos policy
----------

**Minimum user role:** operator

A QoS policy is a set of rules and is identified by a unique name.

To create a QoS policy:

**Command syntax: policy [policy]**

**Command mode:** config

**Hierarchies**

- qos

**Note**

- You cannot remove a policy if it is attached to an interface.

- A policy must include a rule with an action. The action can be configured on any rule, including the default.

**Parameter table**

+-----------+----------------------------------------------+------------------+---------+
| Parameter | Description                                  | Range            | Default |
+===========+==============================================+==================+=========+
| policy    | References the configured name of the policy | | string         | \-      |
|           |                                              | | length 1-255   |         |
+-----------+----------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1


**Removing Configuration**

To remove the policy
::

    dnRouter(cfg-qos)# no policy MyQoSPolicy1

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 5.1.0   | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 6.0     | When moving into different modes, higher mode names are removed |
+---------+-----------------------------------------------------------------+
| 9.0     | QoS not supported                                               |
+---------+-----------------------------------------------------------------+
| 11.2    | Command re-introduced                                           |
+---------+-----------------------------------------------------------------+
```

## speeds
```rst
qos policy speeds
-----------------

**Minimum user role:** operator

To configure a policy with the speeds in gbps of local and remote interfaces configured with this policy:

**Command syntax: speeds [speeds]** [, speeds, speeds]

**Command mode:** config

**Hierarchies**

- qos policy

**Note**

- Command is relevant only for NC-AI clusters. Should be used when there are interfaces speeds which exists only in part of the NCPs.

- You should configure all speeds of interfaces using this qos policy, local and remote. Policy must be identical on all NCPs, otherwise the policy will not be applied for remote interfaces.

- The speeds are configured in Gbps.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| speeds    | List of interface speeds (in Gbps) the policy is relevant to. For example, 100   | | 100   | \-      |
|           | for 100Gbps, 200 for 200Gbps, etc.                                               | | 200   |         |
|           |                                                                                  | | 400   |         |
|           |                                                                                  | | 800   |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy MyQoSPolicy1
    dnRouter(cfg-policy-MyQoSPolicy1)# speeds 100, 200, 400, 800


**Removing Configuration**

To remove a speed configured for a policy:
::

    dnRouter(cfg-policy-MyQoSPolicy1)# no speeds 100

To remove all speeds configured for a policy:
::

    dnRouter(cfg-policy-MyQoSPolicy1)# no speeds

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## max-bandwidth
```rst
qos port-mirroring max-bandwidth
--------------------------------

**Minimum user role:** operator

The port mirroring shaper ensures that the rate of unscheduled port mirroring traffic recycled by each NCP core is limited to the shaper rate.
To configure the rate of unscheduled port mirroring traffic:

**Command syntax: max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos port-mirroring

**Parameter table**

+---------------------+---------------------------------------------+------------+---------+
| Parameter           | Description                                 | Range      | Default |
+=====================+=============================================+============+=========+
| max-bandwidth-mbits | Per NCP Port Mirroring shaper rate in mbits | 50-1200000 | 1200000 |
+---------------------+---------------------------------------------+------------+---------+
| units               |                                             | | mbps     | mbps    |
|                     |                                             | | gbps     |         |
+---------------------+---------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# port-mirroring
    dnRouter(cfg-qos-port-mirroring)# max-bandwidth 10 Gbps


**Removing Configuration**

To revert the configured rate back to its default value:
::

    dnRouter(cfg-qos)# no port-mirroring max-bandwidth

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+
```

## port-mirroring
```rst
qos port-mirroring
------------------

**Minimum user role:** operator

Port mirroring QoS adds a shaper for recycled port mirroring traffic and ensures that it is limited to the specified shaper rate.

To enter the Port Mirroring QoS configuration hierarchy:

**Command syntax: port-mirroring**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# port-mirroring
    dnRouter(cfg-qos-port-mirroring)#


**Removing Configuration**

To revert the port mirroring parameters back to default:
::

    dnRouter(cfg-qos)# no port-mirroring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
qos priority-flow-control admin-state
-------------------------------------

**Minimum user role:** operator

To enable/disable priority-based flow control:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Parameter table**

+-------------+----------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                          | Range        | Default  |
+=============+======================================================================+==============+==========+
| admin-state | The administrative state of the priority-based flow control feature. | | enabled    | disabled |
|             |                                                                      | | disabled   |          |
+-------------+----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# admin-state enabled
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-qos-pfc)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## global-clear-threshold
```rst
qos priority-flow-control global-clear-threshold
------------------------------------------------

**Minimum user role:** operator

If VSQ size for a particular queue is less than the clear-threshold value, the transmission of PFC pause frames will be stopped. Lower hierarchies use global thresholds unless they have their own specific configuration. To configure the global PFC clear threshold on the interface that shall apply for each traffic class:

**Command syntax: global-clear-threshold [global-clear-threshold] [units]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- Default clear-threshold is 80kbytes. An explicit configuration for a specific traffic class takes precendence over the inherited global configuration.

- Clear-threshold must be lower than the global pause-threshold or the traffic class specific pause-threshold

**Parameter table**

+------------------------+-----------------------------------------------------------------------------+-------------+---------+
| Parameter              | Description                                                                 | Range       | Default |
+========================+=============================================================================+=============+=========+
| global-clear-threshold | The PFC clear-threshold value is the VSQ size to stop sending pause frames. | 0-199999744 | 80000   |
+------------------------+-----------------------------------------------------------------------------+-------------+---------+
| units                  |                                                                             | | bytes     | bytes   |
|                        |                                                                             | | kbytes    |         |
|                        |                                                                             | | mbytes    |         |
+------------------------+-----------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# global-clear-threshold 100 kbytes


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-qos-pfc)# no clear-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## global-pause-threshold
```rst
qos priority-flow-control global-pause-threshold max-threshold
--------------------------------------------------------------

**Minimum user role:** operator

The global pause threshold is set dynamically between a minimum and maximum value, proportional to the amount of free buffer resources. The slope between the minimum and maximum values is determined by the alpha parameter. As the amount of free buffer resources increases, the pause threshold increases. When the size of a VSQ exceeds the PFC pause threshold, PFC pause frames are sent to the peer until the queue size falls below the clear threshold. Lower hierarchies use global thresholds unless they have their own specific configuration. to configure the global pause threshold:

**Command syntax: global-pause-threshold max-threshold [global-max-pause-threshold] [units1] min-threshold [global-min-pause-threshold] [units2] alpha [global-alpha]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- The default pause-threshold is 200KB. An explicit configuration for a specific traffic class takes precedence over the inherited global configuration. To use dynamic PFC set the global-min-pause-threshold to be lower than the global-max-pause-threshold and add the global-alpha.

- The clear-threshold must be lower than the global pause-threshold or the traffic class specific pause-threshold.

- The dynamic PFC formula (FADT): 

- If a free resource/(2^alpha) is bigger than the max-threshold => threshold=max-threshold

- If a free resource/(2^alpha) is smaller than min-threshold (low resources) => threshold=min-threshold

- If the max-threshold > free-resource/(2^alpha) > min-threshold => threshold=free-resource/(2^alpha)

**Parameter table**

+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| Parameter                  | Description                                                                      | Range         | Default |
+============================+==================================================================================+===============+=========+
| global-max-pause-threshold | The PFC max pause threshold is the max VSQ size to start triggering pause        | 256-200000000 | 200000  |
|                            | frames.                                                                          |               |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| units1                     |                                                                                  | | bytes       | bytes   |
|                            |                                                                                  | | kbytes      |         |
|                            |                                                                                  | | mbytes      |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| global-min-pause-threshold | The PFC min pause threshold is the min VSQ size to start triggering pause        | 256-200000000 | 200000  |
|                            | frames.                                                                          |               |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| units2                     |                                                                                  | | bytes       | bytes   |
|                            |                                                                                  | | kbytes      |         |
|                            |                                                                                  | | mbytes      |         |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+
| global-alpha               | PFC alpha sets the dynamic threshold slope.                                      | 0-8           | 4       |
+----------------------------+----------------------------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# global-pause-threshold max-threshold 300 kbytes min-threshold 150 kbytes global-alpha 4
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To revert to the default value
::

    dnRouter(cfg-qos-pfc)# no pause-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## lossless-threshold
```rst
qos priority-flow-control lossless-pause-threshold lossless-clear-threshold
---------------------------------------------------------------------------

**Minimum user role:** operator

When the size of a global-VSQ exceeds the PFC pause threshold (in percentages), PFC pause frames are sent to all PFC enabled peers until the global-VSQ size falls below the lossless-clear threshold.

**Command syntax: lossless-pause-threshold [lossless-pause-threshold] lossless-clear-threshold [lossless-clear-threshold]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- There are no default values because the values depend on HBM/SRAM size and states that may vary between installations and devices.

- This command is only active after setting pause-threshold and clear-threshold.

- This command is only active after it was configured even if the priority-flow-control admin-state is enabled.

- When configured, priority-flow-control admin-state enables and disables this command without loosing the configured values.

**Parameter table**

+--------------------------+-------------+-------+---------+
| Parameter                | Description | Range | Default |
+==========================+=============+=======+=========+
| lossless-pause-threshold | percentage  | 0-100 | \-      |
+--------------------------+-------------+-------+---------+
| lossless-clear-threshold | percentage  | 1-100 | \-      |
+--------------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# lossless-pause-threshold 10 lossless-clear-threshold 11
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To remove the command:
::

    dnRouter(cfg-qos-pfc)# no lossless-pause-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## lossy-threshold
```rst
qos priority-flow-control lossy-threshold
-----------------------------------------

**Minimum user role:** operator

When the lossy global VSQ size is above the lossy-threshold value, lossy packets are dropped. To configure the lossy global VSQ size threshold:

**Command syntax: lossy-threshold [lossy-threshold]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Note**

- This command has no defaults.

- This command is only active once the threshold is set.

- This command is active ONLY after it has been configured even if the priority-flow-control admin-state is enabled.

- When configured, priority-flow-control admin-state enables and disables this command without loosing the configured values.

- When a lossy threshold is triggered, tail-drop will apply to all interfaces on all traffic-classes except traffic-classes that are set as lossless on all interfaces.

**Parameter table**

+-----------------+-------------+-------+---------+
| Parameter       | Description | Range | Default |
+=================+=============+=======+=========+
| lossy-threshold | percentage  | 0-100 | \-      |
+-----------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# lossy-threshold 10


**Removing Configuration**

To remove the command:
::

    dnRouter(cfg-qos-pfc)# no lossy-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## priority-flow-control
```rst
qos priority-flow-control
-------------------------

**Minimum user role:** operator

Priority Flow Control (PFC; IEEE 802.1Qbb), also referred to as Class-based Flow Control (CBFC) or Per Priority Pause (PPP), is a mechanism that prevents frame loss due to congestion.
PFC is similar to 802.3x Flow Control (pause frames) or Link-level Flow Control (LFC), however, PFC functions on a per class-of-service (CoS) basis.
To enter the global PFC configuration:"

**Command syntax: priority-flow-control**

**Command mode:** config

**Hierarchies**

- qos

**Note**
- Enter this hierarchy to set PFC configuration that will be inherited by all physical interfaces running PFC when no explicit configuration is specified per interface to override the global configuration.

- You can view the PFC administrative state on an interface using the show interfaces detail command. See "show interfaces detail".

- To view PFC counters use the show PFC counters command. See "show priority-flow-control interfaces counters".

- To view PFC queues use the show PFC queues command. See "show priority-flow-control interfaces queues".

**Example**
::

    dnRouter# configure
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To revert all PFC settings to their default values:
::

    dnRouter(cfg-qos)# no priority-flow-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## traffic-class-admin-state
```rst
qos priority-flow-control global-traffic-class admin-state
----------------------------------------------------------

**Minimum user role:** operator

To enable/disable priority-based flow control on a traffic-class:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control global-traffic-class

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state of the priority-based flow control feature for the      | | enabled    | \-      |
|             | specific Traffic-class.                                                          | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# admin-state enabled
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-qos-pfc)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
```

## qos global-policy-map default-ip dscp
```rst
qos global-policy-map default-ip dscp
-------------------------------------

**Minimum user role:** operator

To change the default PHB selection for IP traffic:

**Command syntax: dscp [dscp] qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-ip 

**Parameter table**

+---------------+-----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
|               |                       |                                                                                                                                                                                                                                  |             |
| Parameter     | Description           | Range                                                                                                                                                                                                                            | Default     |
+===============+=======================+==================================================================================================================================================================================================================================+=============+
|               |                       |                                                                                                                                                                                                                                  |             |
| dscp          | The DSCP value        | 0..63 or named DSCP value:                                                                                                                                                                                                       | \-          |
|               |                       |                                                                                                                                                                                                                                  |             |
|               |                       | DEFAULT(0), CS1(8), CS2(16), CS3(24), CS4(32),   CS5(40), CS6(48), CS7(56), AF11(10), AF12(12), AF13(14), AF21(18),   AF22(20),AF23(22),AF31(26), AF32(28), AF33(30), AF41(34), AF42(36), AF43(38),   EF(46), VOICE-ADMIT(44)    |             |
+---------------+-----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
|               |                       |                                                                                                                                                                                                                                  |             |
| qos-tag       | The QoS-tag value     | 0..7                                                                                                                                                                                                                             | \-          |
+---------------+-----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
|               |                       |                                                                                                                                                                                                                                  |             |
| drop-tag      | The drop-tag value    | green                                                                                                                                                                                                                            | green       |
|               |                       |                                                                                                                                                                                                                                  |             |
|               |                       | yellow                                                                                                                                                                                                                           |             |
+---------------+-----------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-ip
  dnRouter(cfg-qos-default-ip)#
  dnRouter(cfg-qos-default-ip)# dscp cs1 qos-tag 2 drop-tag yellow
  dnRouter(cfg-qos-default-ip)# dscp 1 qos-tag 2


**Removing Configuration**

To revert to the default value:
::

  dnRouter(cfg-qos-default-ip)# no dscp cs1


.. **Help line:** configure qos IP default phb selection

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+```

## qos global-policy-map default-ip ipp
```rst
qos global-policy-map default-ip ipp
------------------------------------

**Minimum user role:** operator

This command sets all the default calss map entries corresponding to the IP precedence bits to a specified common qos-tag and drop-tag tuple.

For example, **ipp 1 qos-tag 3** will set dscp 8,9,10,11,12,13,14,15 entries in the map to qos-tag 3 and drop-tag green.

To change the default PHB selection for IP traffic based on IP precedence:

**Command syntax: ipp [ipp] qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-ip

**Parameter table**

+---------------+----------------------------+-----------+-------------+
|               |                            |           |             |
| Parameter     | Description                | Range     | Default     |
+===============+============================+===========+=============+
|               |                            |           |             |
| ipp           | The IP precedence value    | 0..7      | \-          |
+---------------+----------------------------+-----------+-------------+
|               |                            |           |             |
| qos-tag       | The QoS-tag value          | 0..7      | \-          |
+---------------+----------------------------+-----------+-------------+
|               |                            |           |             |
| drop-tag      | The drop-tag value         | green     | green       |
|               |                            |           |             |
|               |                            | yellow    |             |
+---------------+----------------------------+-----------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-ip
  dnRouter(cfg-qos-default-ip)#
  dnRouter(cfg-qos-default-ip)# ipp 4 qos-tag 2 drop-tag yellow

The following example the command will set the DSCP 8, 9, 10, 11, 12, 13, 14, and 15 entries in the map to qos-tag 3 and drop-tag green:
::

  dnRouter(cfg-qos-default-ip)# ipp 5 qos-tag 3


**Removing Configuration**

To revert to the default value:
::

  dnRouter(cfg-qos-default-ip)#no ipp 4


.. **Help line:** configure qos IP default phb selection

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+```

## qos global-policy-map default-l2
```rst
qos global-policy-map default-l2
--------------------------------

**Minimum user role:** operator

To configure a default qos-tag and drop-tag tuple for L2 traffic:

**Command syntax: qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-l2 

**Parameter table**

+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| Parameter     | Description           | Range     | Default     |
+===============+=======================+===========+=============+
|               |                       |           |             |
| qos-tag       | The QoS-tag value     | 0..7      | \-          |
+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| drop-tag      | The drop-tag value    | green     | green       |
|               |                       |           |             |
|               |                       | yellow    |             |
+---------------+-----------------------+-----------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-l2
  dnRouter(cfg-qos-default-l2)#
  dnRouter(cfg-qos-default-l2)# qos-tag 6
  dnRouter(cfg-qos-default-l2)# qos-tag 6 drop-tag green

**Removing Configuration**

To revert the map configuration to default:
::

  dnRouter(cfg-qos-default-l2)#no qos-tag

.. **Help line:** configure qos layer 2 default-class map entry

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+```

## qos global-policy-map default-mpls mpls-exp
```rst
qos global-policy-map default-mpls mpls-exp
-------------------------------------------

**Minimum user role:** operator

To configure the default QoS MPLS PHB selection:

**Command syntax: mpls-exp [mpls-exp] qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-ip

**Parameter table**

+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| Parameter     | Description           | Range     | Default     |
+===============+=======================+===========+=============+
|               |                       |           |             |
| mpls-exp      | The MPLS exp value    | 0..7      | \-          |
+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| qos-tag       | The QoS-tag value     | 0..7      | \-          |
+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| drop-tag      | The drop-tag value    | green     | green       |
|               |                       |           |             |
|               |                       | yellow    |             |
+---------------+-----------------------+-----------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-mpls
  dnRouter(cfg-qos-default-mpls)#
  dnRouter(cfg-qos-default-mpls)# mpls-exp 2 qos-tag 3
  dnRouter(cfg-qos-default-mpls)# mpls-exp 2 qos-tag 3 drop-tag yellow


**Removing Configuration**

To revert the default-mpls entry to its default value:
::

  dnRouter(cfg-qos-default-mpls)# no mpls-exp 2

.. **Help line:** configure qos MPLS default phb selection

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+```

## qos global-policy-map
```rst
qos global-policy-map
---------------------

**Minimum user role:** operator

Global policy maps control the traffic's mapping of QoS attributes to per-hop behavior (PHB), i.e. to qos-tag and drop-tag for IP, MPLS and layer-2 traffic not controlled by an interface ingress QoS policy.

You can configure the following global policy maps:

• Default-IP global map: 

  The qos-tag and drop-tag assigned to IP traffic originated and sent from the system to the network ("from-me" traffic) is controlled globally by this map. The mapping is also used as the ingress policy on all interfaces which are not assigned any user policy.

  For example, BGP traffic sent from the NCC will use the assigned BGP DSCP value (configured using the  "protocols bgp class-of-service" command), and will be mapped to qos-tag and drop-tag specified by this map.

  The following table describes the default mapping of DSCP to qos-tag, with drop-tag set to yellow for qos-tags 1 and 3:

  ::

    +-------------+----------+----------+           +-------------+----------+----------+
    | dscp        | qos-tag  | drop-tag |           | dscp        | qos-tag  | drop-tag |
    +-------------+----------+----------+           +-------------+----------+----------+
    | default     | 0        | green    |           | cs4         | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 1           | 0        | green    |           | 33          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 2           | 0        | green    |           | af41        | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 3           | 0        | green    |           | 35          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 4           | 0        | green    |           | af42        | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 5           | 0        | green    |           | 37          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 6           | 0        | green    |           | af43        | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 7           | 0        | green    |           | 39          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | cs1         | 1        | yellow   |           | cs5         | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 9           | 1        | yellow   |           | 41          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af11        | 1        | yellow   |           | 42          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 11          | 1        | yellow   |           | 43          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af12        | 1        | yellow   |           | voice-admit | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 13          | 1        | yellow   |           | 45          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af13        | 1        | yellow   |           | ef          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 15          | 1        | yellow   |           | 47          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | cs2         | 2        | green    |           | cs6         | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 17          | 2        | green    |           | 49          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af21        | 2        | green    |           | 50          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 19          | 2        | green    |           | 51          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af22        | 2        | green    |           | 52          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 21          | 2        | green    |           | 53          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af23        | 2        | green    |           | 54          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 23          | 2        | green    |           | 55          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | cs3         | 3        | yellow   |           | cs7         | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 25          | 3        | yellow   |           | 57          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af31        | 3        | yellow   |           | 58          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 27          | 3        | yellow   |           | 59          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af32        | 3        | yellow   |           | 60          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 29          | 3        | yellow   |           | 61          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af33        | 3        | yellow   |           | 62          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 31          | 3        | yellow   |           | 63          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    
• Default-MPLS global map:

  The qos-tag and drop-tag assigned to MPLS traffic originated and sent from the system to the network ("from-me" traffic) is controlled globally by this map. The mapping is also used as the ingress policy on all interfaces which are not assigned any user policy.

  For example, MPLS Ping packets sent from the NCC will use the assigned BGP exp value (e.g. using the  "run ping" mpls bgp-lu 1.2.3.4/32 count 10 exp 4 command), and will be mapped to qos-tag and drop-tag specified by this map.

  The qos-tag and drop-tag assigned to incoming MPLS packets at tunnel termination, when termination with explicit-null label is used, is also controlled globally by this map. Mapping of all other MPLS traffic, either mid tunnel (swap) or at the penultimate-hop-popping (PHP) tunnel edge are controlled per QoS policy attached to the ingress interface.

  The pipe model requires that the PHB will be selected according to the mpls-exp value of the top-most label, and in particular, when the tunnel is terminated using the explicit-null label (reserved labels 0 or 3 for Ipv6), the PHB is determined from the mpls-exp carried by the explicit null label.

  The following table describes the default mapping of the MPLS exp value to qos-tag, with drop-tag set to yellow for qos-tags 1 and 3:
  ::

    +----------+----------+----------+
    | mpls-exp | qos-tag  | drop-tag |
    +----------+----------+----------+
    | 0        | 0        | green    |
    +----------+----------+----------+
    | 1        | 1        | yellow   |
    +----------+----------+----------+
    | 2        | 2        | green    |
    +----------+----------+----------+
    | 3        | 3        | yellow   |
    +----------+----------+----------+
    | 4        | 4        | green    |
    +----------+----------+----------+
    | 5        | 5        | green    |
    +----------+----------+----------+
    | 6        | 6        | green    |
    +----------+----------+----------+
    | 7        | 7        | green    |
    +----------+----------+----------+

• Default-L2 global map:
  
  The qos-tag and drop-tag assigned to layer 2 traffic originated and sent from the system to the network ("from-me" traffic) is controlled globally by this map. For example, ARP, IS-IS, LLDP, etc.
  
  By default, L2 traffic is assigned qos-tag 6 and drop-tag green.

To configure a QoS global policy map, enter the policy's configuration mode:

**Command syntax: qos global-policy-map [global-policy-map-name]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+---------------------------+---------------------------------------------------+------------------------------------------------------------------------------------+-------------+
|                           |                                                   |                                                                                    |             |
| Parameter                 | Description                                       | Range                                                                              | Default     |
+===========================+===================================================+====================================================================================+=============+
|                           |                                                   |                                                                                    |             |
| global-policy-map-name    | The name of the global policy map to configure    | default-ip: default mapping applicable to from-me   IP traffic                     | \-          |
|                           |                                                   |                                                                                    |             |
|                           |                                                   | default-mpls: default mapping applicable to   from-me / Explicit NULL MPLS traffic |             |
|                           |                                                   |                                                                                    |             |
|                           |                                                   | default-l2: Default mapping. Applicable to   from-me L2 traffic                    |             |
+---------------------------+---------------------------------------------------+------------------------------------------------------------------------------------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-ip
  dnRouter(cfg-qos-default-ip)#

  dnRouter(cfg-qos)# global-policy-map default-mpls
  dnRouter(cfg-qos-default-mpls)#

  dnRouter(cfg-qos)# global-policy-map default-l2
  dnRouter(cfg-qos-default-l2)#


**Removing Configuration**

To remove the global-policy-map configuration:
::

  dnRouter(cfg-qos)# no global-policy-map default-ip
  dnRouter(cfg-qos)# no global-policy-map

.. **Help line:** configure qos global-policy-map

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+```

## qos mib-enable
```rst
qos mib-enable
-------------------

**Minimum user role:** operator

The QoS MIB describes the names and optional description strings of policies, rules and traffic classes, and how the three are combined together. The MIB models the hierarchy between configuration objects (not instances). This has two advantages: it allows the QoS hierarchy to be queried even if no policy is provisioned (attached to an interface), and it ensures that the hierarchy table scale does not increase linearly with the number of provisioned interfaces, therefore requiring less resources for querying all tables when the number of interfaces is large.

To enable QoS telemetry via SNMP:

**Command syntax: qos mib [mib-enable]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+---------------+---------------------------------------------+-------------+-------------+
|               |                                             |             |             |
| Parameter     | Description                                 | Range       | Default     |
+===============+=============================================+=============+=============+
|               |                                             |             |             |
| mib-enable    | To enable/disable QoS telemetry via SNMP    | Enabled     | Disabled    |
|               |                                             |             |             |
|               |                                             | Disabled    |             |
+---------------+---------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# mib enabled


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-qos)# no mib

.. **Help line:** Enable QoS telemetry via SNMP

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+
```

## qos  mpls-swap-exp-edit-mode
```rst
mpls-swap-exp-edit-mode
-----------------------

**Minimum user role:** operator

You can use this command to control whether the MPLS EXP top most label bits (the Traffic Class field) of the swapped header are preserved. 

When the mode is set to **preserve**, EXP bits are always preserved.

When the mode is set to **copy**, the EXP bits are copied from the incoming topmost MPLS header. 

To allow the set mpl-exp command to modify EXP bits, the edit mode must be set to **copy**.

To configure the MPLS swap-exp edit mode:


**Command syntax: mpls-swap-exp-edit-mode [mode]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+---------------+---------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                 |           |             |
| Parameter     | Description                                                                     | Range     | Default     |
+===============+=================================================================================+===========+=============+
|               |                                                                                 |           |             |
| mode          | Define the mode to control the action on the   swapped MPLS header EXP bits.    | Preserve  | Preserve    |
|               |                                                                                 |           |             |
|               |                                                                                 | Copy      |             |
+---------------+---------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# mpls-swap-exp-preserve copy


**Removing Configuration**

To return the parameter to the default:
::

	dnRouter(cfg-qos)# no mpls-swap-exp-preserve

.. **Help line:** rule identifier

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+```

## qos overview
```rst
Quality of Service (QoS) Overview
---------------------------------
QoS manages data traffic types and guarantees that high-priority traffic is successfully sent across a congested network with enough bandwidth allowance and without experiencing delay, jitter, or packet loss. For example, QoS can prioritize packets in real-time applications like video and VOIP over FTP or email traffic.

Quality of Service achieves data priority with policies, which are rules to manage network traffic. A rule comprises a traffic-class to match and a list of actions to perform if the traffic-class condition is met. Within a QoS policy, rules are defined in order of execution. Each rule has an ID, which is executed in ascending order. A default rule is implicitly created for each policy, so traffic that does not match any defined rule will match the default rule.

QoS policies are triggered only when the network is congested. Once created, the QoS policy is attached to an ingress or egress interface. For further details, refer to the QOS Feature Guide in the DriveNets Documentation portal https://docs.drivenets.com.```

## qos policy rule default
```rst
qos policy rule default
-----------------------

**Minimum user role:** operator

A single default rule is automatically created for each policy. This is the rule that is applied when no other rule matches the traffic, so it can only be configured with actions, and not with match criteria. The default rule has the lowest rule priority.

On an ingress policy, rule default sets the qos-tag to 0 and drop-tag to green by default.

On an egress policy, rule default uses the df (Default Forwarding) queue by default.

To configure the default rule for the policy:


**Command syntax: rule default**

**Command mode:** config

**Hierarchies**

- qos policy

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# policy MyQoSPolicy1
	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# rule default
	dnRouter(cfg-policy-MyQoSPOlicy1-rule-default)#


**Removing Configuration**

To revert the default rule to its default value:
::

	dnRouter(cfg-qos-policy-MyQoSPOlicy1)# no rule default


.. **Help line:** rule default


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+```

## qos
```rst
qos
----

**Minimum user role:** operator

A Quality of Service (QoS) policy is a set of rules used for managing network bandwidth, delay, jitter, and packet loss. A rule comprises a traffic-class to match and a list of actions to perform if the traffic-class condition is met. Within a QoS policy, rules are defined in order of execution. Each rule has an ID and the rules are executed in ascending order. A default rule is implicitly created for each policy, such that traffic that does not match any of the defined rules will match the default rule.

The QoS policy is attached to interfaces. See "interfaces qos policy".

To enter the qos configuration hierarchy:

**Command syntax: qos**

**Command mode:** config


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos


.. **Removing Configuration**


.. **Help line:**

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 6.0         | Command introduced for new hierarchy    |
+-------------+-----------------------------------------+
|             |                                         |
| 9.0         | QoS not supported                       |
+-------------+-----------------------------------------+
|             |                                         |
| 11.0        | Command reintroduced                    |
+-------------+-----------------------------------------+```

## qos wred-profile
```rst
qos wred-profile
-----------------

**Minimum user role:** operator

The purpose of the Weighted Random Early Detection (WRED) profile is to avoid congestion on the queue by starting to drop packets randomly before the queue reaches its maximum limit. By dropping packets randomly, WRED signals to the sender to slow down the transmission rate (the mechanism accompanies a transport-layer congestion control protocol such as TCP).

The packet drop probability is based on a minimum threshold, a maximum threshold and a linear curve that starts at 0 drop probability and crosses the maximum drop probability threshold at 10%. You can set up to two curves (yellow/green) for AF/DF forwarding classes and up to a total of 16 WRED profiles. 

When configuring the curves for each forwarding class, you should take into account the queue's size (see "qos policy rule action queue size"). You can then decide when each curve should start dropping packets. You should set the minimum threshold high enough to maximize the utilization of the queue capacity. The minimum threshold should not be higher than the queue size configured for the forwarding class.

When the average queue size crosses the min-threshold, WRED begins to drop packets randomly. The drop probability increases until the average queue size reaches the maximum threshold. When the average queue size exceeds the maximum threshold, all packets are dropped.


.. The average queue size is calculated as follows:

To configure a WRED profile:

#.	Enter WRED profile configuration hierarchy (see below)
#.	Configure a curve.

**Command syntax: wred-profile [profile-name]**
**Command syntax: wred-profile [profile-name] curve {green|yellow}** min [min-value] [min-knob] max [max-value] [max-knob] max-drop [max-drop]

**Command mode:** config

**Hierarchies**

- qos 

**Note**

- The average queue size refers to the (ingress) virtual output queue (VOQ). 

- To allow small bursts with no drops, the min- and max-values relate to the average queue size and not to the current queue size.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| Parameter       | Description                                                                                                                                                                                                                    | Range                     | Default     |
+=================+================================================================================================================================================================================================================================+===========================+=============+
|                 |                                                                                                                                                                                                                                |                           |             |
| profile-name    | The name of the profile. If the profile name   already exists, the command will update the values of the parameters. If the   profile name does not exist, a new profile is created with the configured   parameter values.    | String                    |  \-         |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| min-value       | Specify the lower value for the range of the   curve, below which no packets will be dropped.                                                                                                                                  | 1..2000000 (microseconds) | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 | The min-value must be less or equal to the   max-value                                                                                                                                                                         | 1..200 (milliseconds)     |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| min-knob        | Set the unit of measurement for the min value                                                                                                                                                                                  | microseconds              | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 |                                                                                                                                                                                                                                | milliseconds              |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| max-value       | Specify the upper value for the range of the curve,   above which all packets will be dropped.                                                                                                                                 | 1..2000000 (microseconds) | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 | The max-value must be equal or greater than   min-value.                                                                                                                                                                       | 1..200 (milliseconds)     |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| max-knob        | Set the unit of measurement for the max value                                                                                                                                                                                  | microseconds              | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 |                                                                                                                                                                                                                                | milliseconds              |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| max-drop        | The maximum drop probability per curve                                                                                                                                                                                         | 1..100%                   | 10%         |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# wred-profile my_profile
	dnRouter(cfg-qos-wred-profile-my_profile)# curve green min 500 milliseconds max 1000 milliseconds
	dnRouter(cfg-qos-wred-profile-my_profile)# curve yellow min 100 milliseconds max 800 milliseconds

	dnRouter(cfg-qos)# wred-profile my_profile2
	dnRouter(cfg-qos-wred-profile-my_profile2)# curve green min 10 milliseconds max 100 milliseconds


**Removing Configuration**

You cannot delete a WRED profile if it is attached to a queue. You must first delete the profile from the queue. See "qos policy rule action queue wred-profile".

To remove the WRED profile configuration:
::

	dnRouter(cfg-qos)# no wred-profile
	dnRouter(cfg-qos)# no wred-profile my_profile


To remove a curve from the profile:
::

	dnRouter(cfg-qos-wred-profile-default)# no curve green


.. **Help line:** Configure wred curves per drop priority

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 5.1.0       | Command introduced                      |
+-------------+-----------------------------------------+
|             |                                         |
| 6.0         | Applied   new hierarchy                 |
+-------------+-----------------------------------------+
|             |                                         |
| 9.0         | Command not supported                   |
+-------------+-----------------------------------------+
|             |                                         |
| 11.4        | Command reintroduced with new syntax    |
+-------------+-----------------------------------------+
|             |                                         |
| 15.1        | Added support for max-drop              |
+-------------+-----------------------------------------+
|             |                                         |
| 18.3        | Added min-threshold knob                |
+-------------+-----------------------------------------+
| 25.2        | Command syntax change                   |
+-------------+-----------------------------------------+```

## description
```rst
qos traffic-class-map description
---------------------------------

**Minimum user role:** operator

To add a meaningful description for a traffic-class-map:

**Command syntax: description [descr]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+-------------------------------+------------------+---------+
| Parameter | Description                   | Range            | Default |
+===========+===============================+==================+=========+
| descr     | Traffic class map description | | string         | \-      |
|           |                               | | length 1-255   |         |
+-----------+-------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# description "Emergency Traffic"


**Removing Configuration**

To remove the description from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## dscp-ipv4
```rst
qos traffic-class-map dscp-ipv4
-------------------------------

**Minimum user role:** operator

To Configure the traffic-class map dscp-ipv4:

**Command syntax: dscp-ipv4 [dscp-ipv4]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| dscp-ipv4 | Match DSCP for IPv4 | 0-63  | \-      |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp-ipv4 10,12,14


**Removing Configuration**

To remove the dscp-ipv4 from the traffic-class-map:
::

    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp-ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
```

## dscp-ipv6
```rst
qos traffic-class-map dscp-ipv6
-------------------------------

**Minimum user role:** operator

To Configure the traffic-class map dscp-ipv6:

**Command syntax: dscp-ipv6 [dscp-ipv6]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| dscp-ipv6 | Match DSCP for IPv6 | 0-63  | \-      |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp-ipv6 10,12,14


**Removing Configuration**

To remove the dscp-ipv6 from the traffic-class-map:
::

    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
```

## dscp
```rst
qos traffic-class-map dscp
--------------------------

**Minimum user role:** operator

To Configure the traffic-class map dscp:

**Command syntax: dscp [dscp]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+-------------+-------+---------+
| Parameter | Description | Range | Default |
+===========+=============+=======+=========+
| dscp      | Match DSCP  | 0-63  | \-      |
+-----------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp 10,12,14


**Removing Configuration**

To remove the dscp from the traffic-class-map:
::

    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## dual-pcp-dei
```rst
qos traffic-class-map dual-pcp-dei outer-pcp-dei inner-pcp-dei
--------------------------------------------------------------

**Minimum user role:** operator

To configure IEEE 802.1p Priority Code Point (PCP-DEI) bits match criteria on dual VLAN:

**Command syntax: dual-pcp-dei outer-pcp-dei [outer-pcp-dei] inner-pcp-dei [inner-pcp-dei]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+---------------+--------------------------------------+-------+---------+
| Parameter     | Description                          | Range | Default |
+===============+======================================+=======+=========+
| outer-pcp-dei | Outer VLAN Priority Code Point value | \-    | \-      |
+---------------+--------------------------------------+-------+---------+
| inner-pcp-dei | Inner VLAN Priority Code Point value | \-    | \-      |
+---------------+--------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dual-pcp-dei outer-pcp-dei 2 inner-pcp-dei 1


**Removing Configuration**

To remove a specific dual-pcp-dei entry from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no dual-pcp-dei outer-pcp-dei OUTER-PCP-DEI inner-pcp-dei INNER-PCP-DEI

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+
```

## dual-pcp
```rst
qos traffic-class-map dual-pcp outer-pcp inner-pcp
--------------------------------------------------

**Minimum user role:** operator

To configure IEEE 802.1p Priority Code Point (PCP) bits match criteria on dual VLAN:

**Command syntax: dual-pcp outer-pcp [outer-pcp] inner-pcp [inner-pcp]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+--------------------------------------+-------+---------+
| Parameter | Description                          | Range | Default |
+===========+======================================+=======+=========+
| outer-pcp | Outer VLAN Priority Code Point value | \-    | \-      |
+-----------+--------------------------------------+-------+---------+
| inner-pcp | Inner VLAN Priority Code Point value | \-    | \-      |
+-----------+--------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dual-pcp outer-pcp 2 inner-pcp 1


**Removing Configuration**

To remove a specific dual-pcp entry from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no dual-pcp outer-pcp OUTER-PCP inner-pcp INNER-PCP

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 25.3    | Command introduced |
+---------+--------------------+
```

## match
```rst
qos traffic-class-map match
---------------------------

**Minimum user role:** operator

To configure the match type:

**Command syntax: match [match-type]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+------------+----------------------------------------------------+-------+---------+
| Parameter  | Description                                        | Range | Default |
+============+====================================================+=======+=========+
| match-type | Define how multiple match criteria will be handled | any   | any     |
+------------+----------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# match any


**Removing Configuration**

To remove the match type from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no match

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## mpls-exp
```rst
qos traffic-class-map mpls-exp
------------------------------

**Minimum user role:** operator

To configure the MPLS experimental bits match criteria:

**Command syntax: mpls-exp [mpls-exp]** [, mpls-exp, mpls-exp]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+--------------------------+-------+---------+
| Parameter | Description              | Range | Default |
+===========+==========================+=======+=========+
| mpls-exp  | MPLS EXP bits (TC field) | 0-7   | \-      |
+-----------+--------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# mpls-exp 1,3,5


**Removing Configuration**

To remove the mpls-exp from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no mpls-exp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## pcp-dei
```rst
qos traffic-class-map pcp-dei
-----------------------------

**Minimum user role:** operator

To configure IEEE 802.1p Priority Code Point (PCP) and Drop Eligible Indicator (DEI) bits match criteria:

**Command syntax: pcp-dei [pcp-dei]** [, pcp-dei, pcp-dei]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+--------------------------------------------------------------+-------+---------+
| Parameter | Description                                                  | Range | Default |
+===========+==============================================================+=======+=========+
| pcp-dei   | IEEE 802.1Q Priority Code Point and Drop eligible indicator. | 0-15  | \-      |
+-----------+--------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# pcp-dei 1,3,5


**Removing Configuration**

To remove the pcp-dei from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no pcp-dei

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## pcp
```rst
qos traffic-class-map pcp
-------------------------

**Minimum user role:** operator

To configure IEEE 802.1p Priority Code Point (PCP) bits match criteria:

**Command syntax: pcp [pcp]** [, pcp, pcp]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+---------------------------------+-------+---------+
| Parameter | Description                     | Range | Default |
+===========+=================================+=======+=========+
| pcp       | IEEE 802.1Q Priority Code Point | 0-7   | \-      |
+-----------+---------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# pcp 1,3,5


**Removing Configuration**

To remove the pcp from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no pcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## precedence-ipv4
```rst
qos traffic-class-map precedence-ipv4
-------------------------------------

**Minimum user role:** operator

To configure IP precedence-ipv4 bits match criteria:

**Command syntax: precedence-ipv4 [precedence-ipv4]** [, precedence-ipv4, precedence-ipv4]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------------+------------------------------+-------+---------+
| Parameter       | Description                  | Range | Default |
+=================+==============================+=======+=========+
| precedence-ipv4 | Match IP precedence for IPv4 | 0-7   | \-      |
+-----------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence-ipv4 1,3,5


**Removing Configuration**

To remove the precedence-ipv4 from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no precedence-ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
```

## precedence-ipv6
```rst
qos traffic-class-map precedence-ipv6
-------------------------------------

**Minimum user role:** operator

To configure IP precedence-ipv6 bits match criteria:

**Command syntax: precedence-ipv6 [precedence-ipv6]** [, precedence-ipv6, precedence-ipv6]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------------+------------------------------+-------+---------+
| Parameter       | Description                  | Range | Default |
+=================+==============================+=======+=========+
| precedence-ipv6 | Match IP precedence for IPv6 | 0-7   | \-      |
+-----------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence-ipv6 1,3,5


**Removing Configuration**

To remove the precedence-ipv6 from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no precedence-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
```

## precedence
```rst
qos traffic-class-map precedence
--------------------------------

**Minimum user role:** operator

To configure IP precedence bits match criteria:

**Command syntax: precedence [precedence]** [, precedence, precedence]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+------------+---------------------+-------+---------+
| Parameter  | Description         | Range | Default |
+============+=====================+=======+=========+
| precedence | Match IP precedence | 0-7   | \-      |
+------------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence 1,3,5


**Removing Configuration**

To remove the precedence from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no precedence

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## qos-tag
```rst
qos traffic-class-map qos-tag
-----------------------------

**Minimum user role:** operator

To Configure QoS tag match criteria:

**Command syntax: qos-tag [qos-tag]** [, qos-tag, qos-tag]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+------------------------+-------+---------+
| Parameter | Description            | Range | Default |
+===========+========================+=======+=========+
| qos-tag   | QoS-tag priority level | 0-7   | \-      |
+-----------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# qos-tag 1,3,5


**Removing Configuration**

To remove the qos-tag from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no qos-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
```

## traffic-class-map
```rst
qos traffic-class-map
---------------------

**Minimum user role:** operator

A QoS traffic-class-map is a set of packet attributes that match criteria identified by a unique name.

To create a QoS traffic-class-map:

**Command syntax: traffic-class-map [traffic-class-map]**

**Command mode:** config

**Hierarchies**

- qos

**Note**

- You cannot remove a traffic-class-map if it is used in a policy.

**Parameter table**

+-------------------+--------------------------------------------------+------------------+---------+
| Parameter         | Description                                      | Range            | Default |
+===================+==================================================+==================+=========+
| traffic-class-map | References the configured name of the classifier | | string         | \-      |
|                   |                                                  | | length 1-255   |         |
+-------------------+--------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1


**Removing Configuration**

To remove the traffic-class-map:
::

    dnRouter(cfg-qos)# no traffic-class-map MyTrafficClass1

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 11.2    | Command re-introduced |
+---------+-----------------------+
```

## vrf-redirect-0-max-bandwidth
```rst
qos vrf-redirect vrf-redirect-0 max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The vrf-redirect-0 shaper ensures that the maximum rate of static route vrf redirect traffic, sent through the recycle interface, is limited to the shaper rate.
The limit protects against vrf redirect traffic overwhelming or competing with incoming traffic at each NCP.
To configure the rate of the vrf-redireect-0 traffic:

**Command syntax: vrf-redirect-0 max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos vrf-redirect

**Parameter table**

+---------------------+-------------------------------------------+---------------+---------+
| Parameter           | Description                               | Range         | Default |
+=====================+===========================================+===============+=========+
| max-bandwidth-mbits | Per NCP VRF redirect shaper rate in mbits | 100000-400000 | 100000  |
+---------------------+-------------------------------------------+---------------+---------+
| units               |                                           | | mbps        | mbps    |
|                     |                                           | | gbps        |         |
+---------------------+-------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# vrf-redirect
    dnRouter(cfg-qos-vrf-red)# vrf-redirect-0 max-bandwidth 110 Gbps


**Removing Configuration**

To revert the configured rate to the default value:
::

    dnRouter(cfg-qos)# no vrf-redirect vrf-redirect-0 max-bandwidth

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 16.2    | Command introduced                      |
+---------+-----------------------------------------+
| 17.1    | Default units changed from gbps to mbps |
+---------+-----------------------------------------+
```

## vrf-redirect-1-max-bandwidth
```rst
qos vrf-redirect vrf-redirect-1 max-bandwidth
---------------------------------------------

**Minimum user role:** operator

The vrf-redirect-1 shaper ensures that the maximum rate of flowspec and/or ABF vrf redirect traffic, sent through the recycle interface, is limited to the shaper rate.
The limit protects against vrf redirect traffic overwhelming or competing with incoming traffic at each NCP.
To configure the rate of the vrf-redireect-1 traffic:

**Command syntax: vrf-redirect-1 max-bandwidth [max-bandwidth-mbits] [units]**

**Command mode:** config

**Hierarchies**

- qos vrf-redirect

**Parameter table**

+---------------------+-------------------------------------------+---------------+---------+
| Parameter           | Description                               | Range         | Default |
+=====================+===========================================+===============+=========+
| max-bandwidth-mbits | Per NCP VRF redirect shaper rate in mbits | 100000-400000 | 100000  |
+---------------------+-------------------------------------------+---------------+---------+
| units               |                                           | | mbps        | mbps    |
|                     |                                           | | gbps        |         |
+---------------------+-------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# vrf-redirect
    dnRouter(cfg-qos-vrf-red)# vrf-redirect-1 max-bandwidth 110 Gbps


**Removing Configuration**

To revert the configured rate to the default value:
::

    dnRouter(cfg-qos)# no vrf-redirect vrf-redirect-0 max-bandwidth

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 16.2    | Command introduced                      |
+---------+-----------------------------------------+
| 17.1    | Default units changed from gbps to mbps |
+---------+-----------------------------------------+
```

## vrf-redirect
```rst
qos vrf-redirect
----------------

**Minimum user role:** operator

DNOS supports three types of VRF redirect schemes: static routes redirecting to another VRF, flowspec redirection and ABF redirection to another VRF.
VRF QoS adds two shapers, the vrf-redirect-0 shaper and the vrf-redirect-1 shaper.
vrf-redirect-0 ensures that the maximum rate of static-route redirected traffic is limited to the specified shaper rate.
vrf-redirect-1 ensures that the maximum rate of flowpsec redirect and ABF redirect traffic sent is limited to the specified shaper rate.

**Command syntax: vrf-redirect**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# vrf-redirect
    dnRouter(cfg-qos-vrfr)#


**Removing Configuration**

To revert the vrf-redirect parameters to the default value:
::

    dnRouter(cfg-qos)# no vrf-redirect

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
```

