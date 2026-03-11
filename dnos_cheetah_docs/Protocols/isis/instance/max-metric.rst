protocols isis instance max-metric
----------------------------------

**Minimum user role:** operator

The max-metric command enables to set a maximum value for the IS-IS metric. This is the max-metric that will be used for the "isis instance interface address-family metric" or when "isis instance advertise max-metric" is used. By setting a maximum metric value to an interface, you are maximally reducing the chances of selecting that interface for best path calculation.

To set a new max-metric value:


**Command syntax: max-metric [max-metric]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Parameter table**

+------------+------------------------------------+------------+----------+
| Parameter  | Description                        | Range      | Default  |
+============+====================================+============+==========+
| max-metric | Sets the value for maximum metric. | 1-16777215 | 16777214 |
+------------+------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# max-metric 16777214


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-isis-inst)# no max-metric

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 10.0    | Command introduced                  |
+---------+-------------------------------------+
| 13.0    | Modified max-metric parameter range |
+---------+-------------------------------------+
