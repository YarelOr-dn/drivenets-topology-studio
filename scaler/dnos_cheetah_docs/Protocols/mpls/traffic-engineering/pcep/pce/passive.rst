protocols mpls traffic-engineering pcep pce priority passive
------------------------------------------------------------

**Minimum user role:** operator

Support PCE in "passive" mode. Passive PCE is never used for delegation, nor by operational failure of active PCEs or via config. PCC will send all PCRpt messages for all LSPs to the Passive PCE
To configure PCE as passive:

**Command syntax: passive [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep pce priority

**Parameter table**

+-------------+-----------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                 | Range        | Default  |
+=============+=============================================================================+==============+==========+
| admin-state | set whether the pce server is passive thus no delegation will be pass to it | | enabled    | disabled |
|             |                                                                             | | disabled   |          |
+-------------+-----------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# traffic-engineering
    dnRouter(cfg-protocols-mpls-te)# pcep
    dnRouter(cfg-mpls-te-pcep)# pce priority 1 address 1.1.1.1
    dnRouter(cfg-te-pcep-pce)# passive enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-te-pcep-pce)# no passive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
