system diagnostics monitor test component interval
--------------------------------------------------

**Minimum user role:** operator

Configure the diagnostics monitor test interval.

**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- system diagnostics monitor test component

**Parameter table**

+-----------+--------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                              | Range  | Default |
+===========+==========================================================================+========+=========+
| interval  | the period of time that passed from the beginning of the test execution. | 1-3600 | 60      |
+-----------+--------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)# monitor
    dnRouter(cfg-system-diagnostics-monitor)# test punt-datapath
    dnRouter(cfg-diagnostics-monitor-test)# component ncp 0
    dnRouter(cfg-diagnostics-monitor-test-component)# interval 3


**Removing Configuration**

To revert interval to default:
::

    dnRouter(cfg-diagnostics-monitor-test-component)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
