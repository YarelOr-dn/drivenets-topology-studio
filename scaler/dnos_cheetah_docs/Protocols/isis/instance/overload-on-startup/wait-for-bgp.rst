protocols isis instance overload on-startup wait-for-bgp
--------------------------------------------------------

**Minimum user role:** operator

Configure the maximum interval that IS-IS will advertise the overload-bit or max-metric, upon process start, until BGP convergence is completed.

To set the bgp delay time:


**Command syntax: wait-for-bgp** bgp-delay [bgp-delay]

**Command mode:** config

**Hierarchies**

- protocols isis instance overload on-startup

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| bgp-delay | The time (in seconds) where IS-IS is considered to be overloaded after bgp       | 0-86400 | 0       |
|           | convergence has completed                                                        |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# overload on-startup
    dnRouter(cfg-isis-inst-overload)# wait-for-bgp

    dnRouter(cfg-isis-inst-overload)# wait-for-bgp bgp-delay 120


**Removing Configuration**

To revert *bgp-delay* to the default value:
::

    dnRouter(cfg-isis-inst-overload)# no wait-for-bgp bgp-delay

To disable the *wait-for-bgp* constraint and revert *bgp-delay* to the default value:
::

    dnRouter(cfg-isis-inst-overload)# no wait-for-bgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
