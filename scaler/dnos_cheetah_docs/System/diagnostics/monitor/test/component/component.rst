system diagnostics monitor test component
-----------------------------------------

**Minimum user role:** operator

To configure the test parameters for the NCP:

Say you have a cluster with four NCPs (NCP 0-NCP3) and you configure the test as follows:

  - Configure "all" to admin-state enabled and interval 20 seconds.

  - Configure NCP 0 to admin-state disabled.

This means that the test will run every 20 seconds on all NCPs except NCP 0.

If you then change the admin-state for NCP 0 to enabled, the test will run on all NCPs as follows:

  - NCP 0 - every 60 seconds

  - NCP 1-3 - every 20 seconds

**Command syntax: component [component-type] [node-id]**

**Command mode:** config

**Hierarchies**

- system diagnostics monitor test

**Note**

- validation that ncp-id is according to cluster type.

- show in autocomplete only components that are relevant to the test.

- behaves as following, e.g. NCPSs 0-3 available in the cluster.

- the configuration as configured above ncp 0,1 are explicitly configured, means their configuration won't be impacted by component ncp all command.

- ncp 2,3 will be configured with the 'component ncp all' configuration.

- in case user would make implicit configuration for 'component ncp 2' it will override the previous configuration configured by the 'component ncp all'.

- 'all' configuration would be applied (dynamically) also on NCPs that will be added after the system diagnostics configuration was committed.

**Parameter table**

+----------------+----------------------------------------------------+-------+---------+
| Parameter      | Description                                        | Range | Default |
+================+====================================================+=======+=========+
| component-type | References the configured component.               | ncp   | \-      |
+----------------+----------------------------------------------------+-------+---------+
| node-id        | References the configured node-id of the component | \-    | \-      |
+----------------+----------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)# monitor
    dnRouter(cfg-system-diagnostics-monitor)# test punt-datapath
    dnRouter(cfg-diagnostics-monitor-test)# component ncp 0
    dnRouter(cfg-diagnostics-monitor-test)# component ncp 1
    dnRouter(cfg-diagnostics-monitor-test)# component ncp all


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-diagnostics-monitor-test)# no component ncp 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
