protocols pim maximum-mfib-routes
---------------------------------

**Minimum user role:** operator

To configure the PIM maximum MFIB routes limit:

**Command syntax: maximum-mfib-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols pim

**Parameter table**

+-----------+----------------------------------+---------+---------+
| Parameter | Description                      | Range   | Default |
+===========+==================================+=========+=========+
| maximum   | maximum limit of PIM MFIB routes | 1-60000 | 60000   |
+-----------+----------------------------------+---------+---------+
| threshold | percentage of maximum limit      | 1-100   | 75      |
+-----------+----------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# maximum-mfib-routes 50000
    dnRouter(cfg-protocols-pim)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# maximum-mfib-routes 40000 threshold 90
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no maximum-mfib-routes

**Command History**

+---------+---------------------+
| Release | Modification        |
+=========+=====================+
| 12.0    | Command introduced  |
+---------+---------------------+
| 18.2.1  | Renamed the command |
+---------+---------------------+
