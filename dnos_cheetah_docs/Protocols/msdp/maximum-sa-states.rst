protocols msdp maximum-sa-states
--------------------------------

**Minimum user role:** operator

When a PIM Register (S,G) message is received from the RPF, an SA state is created.

You can use the following command to configure the maximum number of SA states.

**Command syntax: maximum-sa-states [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- Threshold - the percentage of the value specified by **maximum**

- 'no maximum-sa-states' command reverts back both the maximum-sa-states and threshold to their default values.

**Parameter table**

+-----------+-----------------------------+---------+---------+
| Parameter | Description                 | Range   | Default |
+===========+=============================+=========+=========+
| maximum   | maximum limit of SA states  | 1-60000 | 60000   |
+-----------+-----------------------------+---------+---------+
| threshold | percentage of maximum limit | 1-100   | 75      |
+-----------+-----------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# maximum-sa-states 18000
    dnRouter(cfg-protocols-msdp)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# maximum-sa-states 20000 threshold 90
    dnRouter(cfg-protocols-msdp)#


**Removing Configuration**

To return the maximum-sa-states to the default value:
::

    dnRouter(cfg-protocols-msdp)# no maximum-sa-states

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
