protocols isis instance flex-algo participate advertise
-------------------------------------------------------

**Minimum user role:** operator

To configure the flexible algorithm profile definition to be advertised within the Flex-Algo domain:

**Command syntax: advertise [flex-algo definition name]** priority [priority]

**Command mode:** config

**Hierarchies**

- protocols isis instance flex-algo participate

**Note**

- Priority is used to define the router priority among the Flex-Algo domain as the selected router to set the Flex-Algo definition.

- The FAD of the router with the highest priority is selected. If there are multiple routers with the same priority, the router with the highest IS-IS system-id is selected.

**Parameter table**

+---------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter                 | Description                                                                      | Range            | Default |
+===========================+==================================================================================+==================+=========+
| flex-algo definition name | The local flex algo profile to be advertise for a specific flex algo id          | | string         | \-      |
|                           | participation                                                                    | | length 1-255   |         |
+---------------------------+----------------------------------------------------------------------------------+------------------+---------+
| priority                  | Indicates the priority for this algorithm                                        | 0-255            | 128     |
+---------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-isis-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# advertise MIN_DELAY_130

    dnRouter(cfg-protocols-isis-inst)# flex-algo
    dnRouter(cfg-isis-inst-flex-algo)# participate 130
    dnRouter(cfg-flex-algo-participate)# advertise MIN_DELAY_130 priority 1


**Removing Configuration**

To revert advertisment priority to default value:
::

    dnRouter(cfg-flex-algo-participate)# no advertise MIN_DELAY_130 priority

To remove advertise configuration:
::

    dnRouter(cfg-flex-algo-participate)# no advertise

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
