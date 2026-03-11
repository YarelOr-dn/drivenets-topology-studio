interfaces clock ptp g8275-1 local-priority
-------------------------------------------

**Minimum user role:** operator

Set the PTP per-port local-priority attribute.

**Command syntax: local-priority [local-priority]**

**Command mode:** config

**Hierarchies**

- interfaces clock ptp g8275-1

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                      | Range | Default |
+================+==================================================================================+=======+=========+
| local-priority | The per port local-priority attribute is used as a tie-breaker in the BMCA data  | 0-255 | 128     |
|                | set comparison algorithm, in the event that all other previous attributes of the |       |         |
|                | data sets being compared are equal. Each parent clock or foreign master clock    |       |         |
|                | data set, whose Announce information was received on the port, is appended with  |       |         |
|                | the local priority attribute of the local port before the BMCA data set          |       |         |
|                | comparison The local priority attribute is not transmitted in Announce messages. |       |         |
+----------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp)# g8275-1
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# local-priority 128

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock ptp g8275-1 local-priority 128


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# no local-priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
