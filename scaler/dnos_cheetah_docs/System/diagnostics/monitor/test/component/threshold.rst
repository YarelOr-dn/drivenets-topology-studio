system diagnostics monitor test component threshold
---------------------------------------------------

**Minimum user role:** operator

Configure the diagnostics monitor test components threshold. The failure-threshold defines the number of allowed consecutive test fails (i.e. the number of consecutive diagnostic packets allowed to be lost). When the threshold is crossed, a single system event is sent, until the threshold is cleared. The threshold is cleared when a diagnostics packet returns.

**Command syntax: threshold [failure-threshold]**

**Command mode:** config

**Hierarchies**

- system diagnostics monitor test component

**Note**

- The number of consecutive allowed test fails, before counting test as failed and issuing a system event.

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter         | Description                                                                      | Range | Default |
+===================+==================================================================================+=======+=========+
| failure-threshold | threshold number of consecutive failed packets for which system events will be   | 1-10  | 3       |
|                   | generated                                                                        |       |         |
+-------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)# monitor
    dnRouter(cfg-system-diagnostics-monitor)# test punt-datapath
    dnRouter(cfg-diagnostics-monitor-test)# component ncp 0
    dnRouter(cfg-diagnostics-monitor-test-component)# threshold 4


**Removing Configuration**

To revert threshold to default:
::

    dnRouter(cfg-diagnostics-monitor-test-component)# no threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
