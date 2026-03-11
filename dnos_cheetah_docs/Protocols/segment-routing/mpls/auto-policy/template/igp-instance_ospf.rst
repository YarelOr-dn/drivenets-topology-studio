protocols segment-routing mpls auto-policy template color igp-instance ospf
---------------------------------------------------------------------------

**Minimum user role:** operator

By default, the SR-TE policies created with auto policy templates are created with the lowest administrative-distance IGP instance.

To configure that SR-TE policies created with a specific SR-TE auto policy template are first attempted to be created in a specific OSPF instance:

**Command syntax: igp-instance ospf [ospf-instance-name]** area [area]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

**Note**
- ISIS is by default preferred over OSPF as a required IGP instance.

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# igp-instance ospf instance_1
    dnRouter(cfg-mpls-auto-policy-color-3)# igp-instance ospf instance_1 area 0


**Removing Configuration**

To revert the igp-instance to its default value:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no igp-instance

To remove the OSPF igp-instance:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no igp-instance ospf instance_1

To revert the desired OSPF area to its default value:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no igp-instance ospf instance_1 area 0

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 18.2    | Command introduced                   |
+---------+--------------------------------------+
| 19.2    | Add optional ospf area configuration |
+---------+--------------------------------------+
