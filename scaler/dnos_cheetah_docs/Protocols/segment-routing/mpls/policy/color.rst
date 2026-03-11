protocols segment-routing mpls policy color
-------------------------------------------

**Minimum user role:** operator

Color distinguishes between different policies with the same source and destination address.

To configure color value for sr-te policy:


**Command syntax: color [color]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Note**

- Color is a mandatory configuration for sr-te policy.

- The user cannot configure more than one policy with the same destination and color.

**Parameter table**

+-----------+------------------------------+--------------+---------+
| Parameter | Description                  | Range        | Default |
+===========+==============================+==============+=========+
| color     | segment-routing policy color | 0-4294967295 | \-      |
+-----------+------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# color 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-sr-mpls-policy)# no color

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
