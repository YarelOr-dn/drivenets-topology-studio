protocols segment-routing mpls auto-policy template color igp-instance isis
---------------------------------------------------------------------------

**Minimum user role:** operator

By default, the SR-TE policies created with auto policy templates are created with the the lowest administrative-distance IGP instance.

To configure that SR-TE policies created with a specific SR-TE auto policy template are first attempted to be created in a specific IS-IS instance:

**Command syntax: igp-instance isis [isis-instance-name]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

**Note**
- ISIS is by default preferred over OSPF as a required IGP instance.

**Parameter table**

+--------------------+---------------------+-------+---------+
| Parameter          | Description         | Range | Default |
+====================+=====================+=======+=========+
| isis-instance-name | IS-IS instance name | \-    | \-      |
+--------------------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# igp-instance isis instance_1


**Removing Configuration**

To revert the igp-instance to its default value:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no igp-instance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
