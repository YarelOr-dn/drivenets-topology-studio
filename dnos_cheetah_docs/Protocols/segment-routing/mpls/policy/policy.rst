protocols segment-routing mpls policy
-------------------------------------

**Minimum user role:** operator

Use a segment-routing policy to forward traffic along a specific path defined as head-end according the list of segments policy uses. When a packet is forwarded according to an SR policy, the SID list (MPLS labels) is pushed on the packet MPLS stack at the policy head-end. The downstream nodes forward the packet according to actions associated with the SID.

A policy may have one of the following states:

•	Up: the policy has at least one valid path and can be used to forward traffic. Only a policy in this state is installed into the forwarding table.
•	Down: the policy has been correctly configured, but it does not contain any valid paths (either path or destination is invalid). In this case, the policy is removed from the forwarding table.
•	Admin-down: the policy has been disabled via the configuration / or by external means of a signaling protocol. The policy is removed from the forwarding table.

The following restrictions apply to policies:

•	You must configure a policy destination.
•	You cannot configure two policies with the same head and destination.

To configure the segment-routing policy:


**Command syntax: policy [policy]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Note**
Required validations:

- policy destination must be configured

- policy color must be configured

- 2 policies from the same head to the same tail with the same color cannot exist


**Parameter table**

+-----------+-----------------------------+------------------+---------+
| Parameter | Description                 | Range            | Default |
+===========+=============================+==================+=========+
| policy    | segment-routing policy name | | string         | \-      |
|           |                             | | length 1-255   |         |
+-----------+-----------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)#


**Removing Configuration**

To remove a specific or all configured policies:
::

    dnRouter(cfg-protocols-sr-mpls)# no policy SR_POLICY_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
