protocols isis instance interface delay-normalization offset
------------------------------------------------------------

**Minimum user role:** operator

To configure the IS-IS delay normalization offset on the interface:

**Command syntax: offset [delay-normalization-offset]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface delay-normalization

**Parameter table**

+----------------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter                  | Description                                                                      | Range        | Default |
+============================+==================================================================================+==============+=========+
| delay-normalization-offset | The value of the delay normalization offset in microseconds. This value must be  | 0-4294967294 | 0       |
|                            | smaller than the value of normalized interval.                                   |              |         |
+----------------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# delay-normalization
    dnRouter(cfg-inst-if-normalization)# offset 3


**Removing Configuration**

To revert the delay normalization offset configuration to its default value:
::

    dnRouter(cfg-inst-if-normalization)# no offset

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
