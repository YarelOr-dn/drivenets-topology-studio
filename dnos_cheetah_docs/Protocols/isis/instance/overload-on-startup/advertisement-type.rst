protocols isis instance overload on-startup advertisement-type
--------------------------------------------------------------

**Minimum user role:** operator

Configure what IS-IS will advertise in the event the system is overloaded upon process start. IS-IS will either advertise overload-bit, max-metric or both. Overload-bit enables IS-IS LSP to signal other routers not to use it as an intermediate hop in their SPF calculations.

Max-metric enables IS-IS to advertise the max-metric value configured for all instance links. When the value is set to 16777214, the router will be considered to be the least preferable in path calculations (but may still be chosen). When the value is set to 16777215, the router will be excluded in path calculations.

To set the IS-IS advertisement-type:


**Command syntax: advertisement-type [advertisement-type]**

**Command mode:** config

**Hierarchies**

- protocols isis instance overload on-startup

**Parameter table**

+--------------------+---------------------------------------------------+---------------------------------+--------------+
| Parameter          | Description                                       | Range                           | Default      |
+====================+===================================================+=================================+==============+
| advertisement-type | Sets what IS-IS will advertise upon process start | | overload-bit                  | overload-bit |
|                    |                                                   | | max-metric                    |              |
|                    |                                                   | | overload-bit-and-max-metric   |              |
+--------------------+---------------------------------------------------+---------------------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# overload on-startup
    dnRouter(cfg-isis-inst-overload)# advertisement-type max-metric


**Removing Configuration**

To revert advertisement-type to default:
::

    dnRouter(cfg-isis-inst-overload)# no advertisement-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
