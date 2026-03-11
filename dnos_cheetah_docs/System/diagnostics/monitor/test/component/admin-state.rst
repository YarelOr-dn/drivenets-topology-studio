system diagnostics monitor test component admin-state
-----------------------------------------------------

**Minimum user role:** operator

To enable/disable the component diagnostics test:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system diagnostics monitor test component

**Note**

- no command set admin-state to the default value

- Upon ``disable``, test execution is immediately stopped.

- All collected stats/thresholds are cleared

**Parameter table**

+-------------+-----------------------------------------------------------+--------------+---------+
| Parameter   | Description                                               | Range        | Default |
+=============+===========================================================+==============+=========+
| admin-state | admin-state of system diagnostics per test per component. | | enabled    | enabled |
|             |                                                           | | disabled   |         |
+-------------+-----------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# diagnostics
    dnRouter(cfg-system-diagnostics)# monitor
    dnRouter(cfg-system-diagnostics-monitor)# test punt-datapath
    dnRouter(cfg-diagnostics-monitor-test)# component ncp 0
    dnRouter(cfg-diagnostics-monitor-test-component)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-diagnostics-monitor-test-component)# no admin-state enabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
