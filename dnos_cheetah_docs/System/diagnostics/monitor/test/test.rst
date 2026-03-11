system diagnostics monitor test
-------------------------------

**Minimum user role:** operator

The system diagnostics infrastructure enables you to run health diagnostics on the system and its components.

The following tests are supported:

- punt-datapath: This test verifies the integrity of the white box chipset packet processing pipeline. It injects a single diagnostics UDP packet at a configured interval from the active routing-engine container to the datapath container over the GRE. The packets are looped back at the processor and returned to the routing-engine container.

To select a test and enter its configuration mode:


**Command syntax: test [test]**

**Command mode:** config

**Hierarchies**

- system diagnostics monitor

**Parameter table**

+-----------+-------------------------------------------------+---------------+---------+
| Parameter | Description                                     | Range         | Default |
+===========+=================================================+===============+=========+
| test      | The type of the test supported for diagnostics. | punt-datapath | \-      |
+-----------+-------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)# monitor
    dnRouter(cfg-system-diagnostics-monitor)# test punt-datapath
    dnRouter(cfg-system-diagnostics-monitor-test)#


**Removing Configuration**

Remove all configured test
::

    dnRouter(cfg-system-util-ncp)# no test

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
