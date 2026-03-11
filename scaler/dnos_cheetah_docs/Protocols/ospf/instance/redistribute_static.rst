protocols ospf instance redistribute static
-------------------------------------------

**Minimum user role:** operator

You can set the router to advertise directly static routes:

**Command syntax: redistribute static** metric [metric] metric-type [metric-type] policy [redistribute-policy] tag [tag] nssa-only

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- By default no redistribution is done.

- The metric default value is set by the redistribute-metric <#ospf redistribute-metric> configuration.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter           | Description                                                                      | Range            | Default |
+=====================+==================================================================================+==================+=========+
| metric              | sets metric value for the redistributed route                                    | 0-16777214       | \-      |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-type         | sets metric-type for the redistributed route                                     | | 1              | 2       |
|                     |                                                                                  | | 2              |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| redistribute-policy | policy (route-map) for filtering the routes                                      | | string         | \-      |
|                     |                                                                                  | | length 1-255   |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| tag                 | The tag value. Tag zero means no tagging is done. If, for example, a static      | 0-4294967295     | \-      |
|                     | route has tag and it is redistributed tag 0 means it is kept with the same tag   |                  |         |
|                     | on the redistributed tag. A non zero tag should override the original static     |                  |         |
|                     | route tag,                                                                       |                  |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+
| nssa-only           | When set, redistributed routes will be advertised only for nssa areas, and will  | \-               | \-      |
|                     | have P bit unset for generated LSA 7 to prevent translation for type 5 LSA       |                  |         |
+---------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 2
    dnRouter(cfg-protocols-ospf-inst)# redistribute static
    dnRouter(cfg-protocols-ospf-inst)# redistribute static metric 1 metric-type 2 policy MY_POL tag 2341	nssa-only


**Removing Configuration**

To return the attribute to the default state:
::

    dnRouter(cfg-protocols-ospf)# no redistribute static

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
| 18.1    | nssa-only added    |
+---------+--------------------+
