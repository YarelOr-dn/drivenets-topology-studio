protocols isis instance address-family ipv4-unicast redistribute static
-----------------------------------------------------------------------

**Minimum user role:** operator

Devices are allowed to redistribute static routes or routes to connected interfaces into IS-IS.

To redistribute routes learned by other means into IS-IS:

**Command syntax: redistribute static** metric [metric-value] policy [policy-name] level [level]

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**
- This option is disabled by default.
-  Redistribution can be done from multiple protocols
-  Metric-type:
.. -  Internal - set IS-IS internal metric type
.. -  External - set IS-IS external metric type

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------------+-----------+
| Parameter    | Description                                                                      | Range            | Default   |
+==============+==================================================================================+==================+===========+
| metric-value | Used to set the allowed routes' metric. By default, routes are redistributed     | 0-16777215       | \-        |
|              | with metric 0.                                                                   |                  |           |
+--------------+----------------------------------------------------------------------------------+------------------+-----------+
| policy-name  | The name of the route-map used. Used to filter and modify redistributed routes.  | | string         | \-        |
|              | ou can set whether to allow or deny the redistribution of the routes that match  | | length 1-255   |           |
|              | the specified policy.                                                            |                  |           |
+--------------+----------------------------------------------------------------------------------+------------------+-----------+
| level        | Specify into which IS-IS level to redistribute routes. When setting level-1-2    | | level-1        | level-1-2 |
|              | routes will be redistributed into both level-1 and level-2.                      | | level-2        |           |
|              |                                                                                  | | level-1-2      |           |
+--------------+----------------------------------------------------------------------------------+------------------+-----------+

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

To stop redistribution of all protocols:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute

To stop redistribution of a specific protocol:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute static

To remove metric modification or policy filtering, or revert to the default level:
::

    dnRouter(cfg-isis-inst-afi)# no redistribute static metric policy

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 6.0     | Command introduced          |
+---------+-----------------------------+
| 9.0     | Command not supported       |
+---------+-----------------------------+
| 10.0    | Command reintroduced        |
+---------+-----------------------------+
| 14.0    | Added support for level-1-2 |
+---------+-----------------------------+
