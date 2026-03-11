protocols isis instance address-family ipv4-unicast redistribute connected
--------------------------------------------------------------------------

**Minimum user role:** operator

Sets the redistribute connected routes into IS-IS:
metric - used to set routes metric. By default routes are redistributed with metric value 0.
policy - used to filter and modify redistributed routes. The user can match the route by "match ip prefix" and set whether to allow or deny routes redistribution. For allowed routes, the user can set isis-metric per specific prefixes
level - define into which isis level redistribute routes. When setting level-1-2 redistribute into both level-1 and level-2. By default, redistribute to both levels.


**Command syntax: redistribute connected** metric [metric] policy [policy] level [level]

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**

- By default, no redistribution is performed.

- Metric-type: - internal - set IS-IS internal metric type. - external - set IS-IS external metric type.

**Parameter table**

+-----------+------------------------------------+------------------+-----------+
| Parameter | Description                        | Range            | Default   |
+===========+====================================+==================+===========+
| metric    | update route metric                | 0-16777215       | \-        |
+-----------+------------------------------------+------------------+-----------+
| policy    | redistribute by policy rules       | | string         | \-        |
|           |                                    | | length 1-255   |           |
+-----------+------------------------------------+------------------+-----------+
| level     | Levels to redistribute routes into | | level-1        | level-1-2 |
|           |                                    | | level-2        |           |
|           |                                    | | level-1-2      |           |
+-----------+------------------------------------+------------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# redistribute connected
    dnRouter(cfg-isis-inst-afi)# redistribute connected metric 100
    dnRouter(cfg-isis-inst-afi)# redistribute connected metric 110 policy MY_POL
    dnRouter(cfg-isis-inst-afi)# redistribute connected level-2
    dnRouter(cfg-isis-inst-afi)# redistribute connected metric 110 policy MY_POL level-1


**Removing Configuration**

To remove connected routes redistribution policy:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute connected policy

To revert connected routes redistribution metric change:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute connected metric

To revert connected routes redistribution for default level:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute connected level

To stop connected routes redistribution:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute connected

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
