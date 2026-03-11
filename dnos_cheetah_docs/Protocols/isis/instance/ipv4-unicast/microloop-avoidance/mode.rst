protocols isis instance address-family ipv4-unicast microloop-avoidance mode
----------------------------------------------------------------------------

**Minimum user role:** operator

Defines the work mode for microloop-avoidance.

- sr-te: Microloop avoidance provides for different cases of network changes, both local and remote. The protecting path is based on sr-te LSP
- hold-lfa: Applies microloop-avoidance for cases of ISIS interface failure by utilizing the existing LFA path as the protection path

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast microloop-avoidance

**Note**

- hold-lfa will only provide protection for prefixes that have an LFA path. Regardless of the LFA type (local, rLFA, ti-lfa)

- in either mode, the post convergence path will be installed after a fib-delay

**Parameter table**

+-----------+----------------------------------------------------+--------------+---------+
| Parameter | Description                                        | Range        | Default |
+===========+====================================================+==============+=========+
| mode      | Define the work more for microloop avoidance logic | | sr-te      | sr-te   |
|           |                                                    | | hold-lfa   |         |
+-----------+----------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# mode hold-lfa


**Removing Configuration**

To revert mode to default:
::

    dnRouter(cfg-inst-afi-uloop)# no mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
