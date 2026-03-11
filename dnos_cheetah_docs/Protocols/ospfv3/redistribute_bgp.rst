protocols ospfv3 redistribute bgp
---------------------------------

**Minimum user role:** operator

You can use the following command to redistribute OSPFV3 routes of the specified protocol or kind into OSPF/OSPFv3, with the metric type and metric set if specified, and filtering the routes using the given policy (if specified).
If indicated, you can add the specified tag:

**Command syntax: redistribute bgp** metric [metric] metric-type [metric-type] policy [redistribute-policy] tag [tag]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- By default no redistribution is done.

- The metric default value is set by `redistribute-metric <#ospfv3 redistribute-metric>` configuration.

- no redistribute [protocol] - stops redistribution of a given protocols.

- no redistribute [protocol] [attribute] - return attribute to default state.

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

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# redistribute bgp
    dnRouter(cfg-protocols-ospfv3)# redistribute bgp metric 1 metric-type 2 policy MY_POL tag 2341


**Removing Configuration**

To return the attribute to the default state:
::

    dnRouter(cfg-protocols-ospfv3)# no redistribute bgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
