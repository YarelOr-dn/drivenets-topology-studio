protocols isis instance address-family ipv6-unicast default-originate
---------------------------------------------------------------------

**Minimum user role:** operator

By default, the default route is distributed only if it is in the RIB and it was not installed from the same IS-IS instance.

To set the IS to distribute a default route to an IS-IS routing domain: 

The default-originate policy command has preference over the always and metric settings, according to the following:

+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| always           | metric           | policy                    | Comment                                                                                                             |
+==================+==================+===========================+=====================================================================================================================+
|                  |                  |                           |                                                                                                                     |
| not set          | not set          | not set                   | default route will not be originated unless it   exists in the RIB                                                  |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| not set          | set              | not set                   | default route will not be originated unless it   exists in the RIB with metric modifications according to policy    |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| set              | not set          | not set                   | default route will be originated with no metric modification                                                        |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| set              | set              | not set                   | default route will not be originated                                                                                |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| not set / set    | not set / set    | set and return "deny"     | default route will always be originated with no   metric modification                                               |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| not set          | not set / set    | set and return "allow"    | default route will be originated if route exists   in rib no metric modification                                    |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+
|                  |                  |                           |                                                                                                                     |
| set              | not set / set    | set and return "allow"    | default route will be originated with metric   modified according to policy                                         |
+------------------+------------------+---------------------------+---------------------------------------------------------------------------------------------------------------------+

**Command syntax: default-originate** always metric [metric-value] policy [policy-name]

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**

- This option is disabled by default. When enabled, the default behavior is to distribute the default route only if the RIB has the default route and it was not installed from the same IS-IS instance.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter    | Description                                                                      | Range            | Default |
+==============+==================================================================================+==================+=========+
| always       | When specified, the default route is always advertised, even when a default      | boolean          | \-      |
|              | route (0.0.0.0/0) is not present in the routing table.                           |                  |         |
+--------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-value | Specifies the cost for reaching the rest of the world through this default       | 1-16777215       | \-      |
|              | route.                                                                           |                  |         |
+--------------+----------------------------------------------------------------------------------+------------------+---------+
| policy-name  | The name of the route-map used.                                                  | | string         | \-      |
|              | Optionally injects the default route conditionally, depending on the matching    | | length 1-255   |         |
|              | conditions in the policy. Possible policy actions are "match rib-has-route" and  |                  |         |
|              | "set isis-metric".                                                               |                  |         |
+--------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# default-originate

    dnRouter(cfg-isis-inst-afi)# default-originate always
    dnRouter(cfg-isis-inst-afi)# default-originate always metric 100

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_2
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# default-originate metric 100

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# default-originate always metric 100

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# default-originate policy DEFAULT_ORIGINATE

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# default-originate always metric 100  policy DEFAULT_ORIGINATE


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-isis-inst-afi)# no default-originate

To disable the always behavior (so that the default route is not advertised unless the route is in the RIB):
::

    dnRouter(cfg-isis-inst-afi)# no default-originate always

To revert the default metric value:
::

    dnRouter(cfg-isis-inst-afi)# no default-originate always metric

To disable the default policy value:
::

    dnRouter(cfg-isis-inst-afi)# no default-originate policy

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 6.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Command not supported         |
+---------+-------------------------------+
| 10.0    | Command reintroduced          |
+---------+-------------------------------+
| 13.0    | Added support for policy-name |
+---------+-------------------------------+
