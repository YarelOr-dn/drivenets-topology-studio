protocols segment-routing mpls policy igp-instance ospf
-------------------------------------------------------

**Minimum user role:** operator

By default, the SR-TE policy is created in the lowest administrative-distance IGP instance.
To configure that SR-TE policy is created in a specific OSPF instance:


**Command syntax: igp-instance ospf [ospf-instance-name]** area [area]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Note**
- ISIS is by default preferred over OSPF as a required IGP instance
- Support for inter-area SR-TE policy follows the following guidelines:
* Policy destination address and algorithm, required to be resolved to SID value. which will define the last SID on stack. Destination may be inter-area route, leading to construct a policy towards ABR advertising the SID
* Explicit path first hop must be a resolvable address / index / label to decide on egress nexthop.
** First hop can be inter-area sid. address expected to be resolved to match SR route. index/label expected to be resolve per local srgb matching the equivalent ILM route result
** For any hop after an inter-area address hop, support only as SID index or absolute label
- If address is given, path will be declared as invalid
- If index is given, the label value will match ABR SRGB base
- For the first inter-area route on the segment-list hops, , require to verify that given index is within the ABR SRGB, otherwise segment-list is invalid
- In case there are ABR ECMP advertising same inter-area SID , only one ABR will be checked to define the absolute label value (per its SRGB base) and the index validity check
- If absolute label is given, the provided label is be imposed , no validation required, no srgb translation

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                                      | Range | Default |
+====================+==================================================================================+=======+=========+
| ospf-instance-name | OSPFv2 instance name                                                             | \-    | \-      |
+--------------------+----------------------------------------------------------------------------------+-------+---------+
| area               | The desired OSPF area for the desired OSPF instance in which SR-TE policy should | \-    | \-      |
|                    | be constructed                                                                   |       |         |
+--------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# igp-instance ospf instance_1

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# igp-instance ospf instance_1 area 0


**Removing Configuration**

To revert the igp-instance to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no igp-instance

To remove the OSPF igp-instance:
::

    dnRouter(cfg-sr-mpls-policy)# no igp-instance ospf instance_1

To revert the desired OSPF area to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no igp-instance ospf instance_1 area 0

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 18.1    | Command introduced                   |
+---------+--------------------------------------+
| 18.2.1  | Add optional ospf area configuration |
+---------+--------------------------------------+
