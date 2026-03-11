protocols isis instance interface delay-normalization interval
--------------------------------------------------------------

**Minimum user role:** operator

To configure the IS-IS delay normalization interval on the interface:

**Command syntax: interval [delay-normalization-interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface delay-normalization

**Parameter table**

+------------------------------+----------------------------------------------------------------+--------------+---------+
| Parameter                    | Description                                                    | Range        | Default |
+==============================+================================================================+==============+=========+
| delay-normalization-interval | The value of the delay normalization interval in microseconds. | 1-4294967295 | \-      |
+------------------------------+----------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# delay-normalization
    dnRouter(cfg-inst-if-normalization)# interval 5


**Removing Configuration**

To remove the delay normalization interval configuration:
::

    dnRouter(cfg-inst-if-normalization)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
