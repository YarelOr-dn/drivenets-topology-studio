protocols isis instance overload on-startup interval
----------------------------------------------------

**Minimum user role:** operator

Configure the maximum interval that IS-IS will advertise the overload-bit or max-metric upon process start.

To set the maximum interval:


**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance overload on-startup

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| interval  | The interval time (in seconds) after system start for which IS-IS will advertise | 5-86400 | 600     |
|           | the overload-bit or max-metric                                                   |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# overload on-startup
    dnRouter(cfg-isis-inst-overload)# interval 300


**Removing Configuration**

To revert interval to default:
::

    dnRouter(cfg-isis-inst-overload)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
