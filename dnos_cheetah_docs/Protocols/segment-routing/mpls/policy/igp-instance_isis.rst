protocols segment-routing mpls policy igp-instance isis
-------------------------------------------------------

**Minimum user role:** operator

By default, the SR-TE policy is created in the lowest administrative-distance IGP instance.
To configure that SR-TE policy is created in a specific IS-IS instance:


**Command syntax: igp-instance isis [isis-instance-name]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

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
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# igp-instance isis instance_1


**Removing Configuration**

To revert the igp-instance to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no igp-instance

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
