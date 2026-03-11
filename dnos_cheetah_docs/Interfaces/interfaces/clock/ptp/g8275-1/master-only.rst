interfaces clock ptp g8275-1 master-only
----------------------------------------

**Minimum user role:** operator

Enable or disable PTP port in Master-only mode.

**Command syntax: master-only [master-only]**

**Command mode:** config

**Hierarchies**

- interfaces clock ptp g8275-1

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| master-only | Set to true when the port can be used only as Master. When the port mode is set  | | enabled    | False   |
|             | to master-only, the port is never placed in the UNCALIBRATED, SLAVE or PASSIVE   | | disabled   |         |
|             | states, and will always attempt to go to the MASTER state. The port state will   |              |         |
|             | remain in PRE-MASTER state if BMC determines that it is connected to a clock     |              |         |
|             | with                                                                             |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# clock
    dnRouter(cfg-if-ge400-0/0/0-clk)# ptp
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp)# g8275-1
    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# master-only enabled

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 clock ptp g8275-1 master-only enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge400-0/0/0-clk-ptp-g8275-1)# no master-only

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
