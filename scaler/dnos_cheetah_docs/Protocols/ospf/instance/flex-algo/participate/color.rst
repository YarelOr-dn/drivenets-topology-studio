protocols ospf instance flex-algo participate color
---------------------------------------------------

**Minimum user role:** operator


By default, participation in the Flex-Algo domain will result in MPLS routes (ILM) for the algorithm known prefix-sids. When the color is set, associate an SR-TE color definition for the Flex-Algo routing domain.
Flex-algo domain routes will be installed in color-mpls-nh table with the configured color, allowing usage to resolve services over the desired color.
Once no fallback is set, it creates a default-route (0.0.0.0/0) with matching color in the color-mpls-nh table. The default-route will be changed to null0, intended for traffic drop.
As a result traffic matching required color, will be dropped if no better solution exists in the mpls-nh table. No fallback to other colors or mpls-nh table will be possible.

To configure color:

**Command syntax: color [color]** no-fallback

**Command mode:** config

**Hierarchies**

- protocols ospf instance flex-algo participate

**Note**

- The color must be unique between all Flex-Algo participation on the same OSPF instance.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| color       | The sr-te color to be assosiated with segment-routing flex-algo routes installed | 0-4294967295 | \-      |
|             | in color-mpls-nh table.                                                          |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+
| no-fallback | create default-route to null0 with matching color in color-mpls-nh table to      | boolean      | \-      |
|             | prevent any fallback rib resolution in case color route was not found            |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance OSPF1
    dnRouter(cfg-protocols-ospf-inst)# flex-algo
    dnRouter(cfg-ospf-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# color 130

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance OSPF-1
    dnRouter(cfg-protocols-ospf-inst)# flex-algo
    dnRouter(cfg-ospf-inst-flex-algo)# participate 100
    dnRouter(cfg-flex-algo-participate)# color 100 no-fallback


**Removing Configuration**

To remove color:
::

    dnRouter(cfg-flex-algo-participate)# no color

To remove color no-fallback:
::

    dnRouter(cfg-flex-algo-participate)# no color 100 no-fallback

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
