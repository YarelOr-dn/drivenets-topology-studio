system ncp clock ptp g8275-1 admin-state
----------------------------------------

**Minimum user role:** operator

Enable PTP clock or disable and remove its configuration.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ncp clock ptp g8275-1

**Note**
- The command is applicable only to UfiSpace NCP3 platform.

**Parameter table**

+-------------+----------------------------------+--------------+----------+
| Parameter   | Description                      | Range        | Default  |
+=============+==================================+==============+==========+
| admin-state | enable/disable PTP functionality | | enabled    | disabled |
|             |                                  | | disabled   |          |
+-------------+----------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# ptp
    dnRouter(cfg-system-ncp-7-clk-ptp)# g8275-1
    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-system-ncp-7-clk-ptp-g8275-1)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
