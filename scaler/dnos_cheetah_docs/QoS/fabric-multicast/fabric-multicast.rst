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
