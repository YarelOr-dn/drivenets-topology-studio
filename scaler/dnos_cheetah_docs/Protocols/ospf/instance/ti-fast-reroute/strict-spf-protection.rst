protocols ospf instance ti-fast-reroute strict-spf-protection
-------------------------------------------------------------

**Minimum user role:** operator

To set if segment-routing can utilize the TI-LFA path for protection of strict-spf prefix-sids:

**Command syntax: strict-spf-protection [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance ti-fast-reroute

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Set if segment-routing can utilize the TI-LFA path for protection of strict-spf  | | enabled    | disabled |
|             | prefix-sids                                                                      | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# ti-fast-reroute
    dnRouter(cfg-protocols-ospf-ti-frr)# strict-spf-protection enabled


**Removing Configuration**

To revert strict-spf-protection to the default value:
::

    dnRouter(cfg-protocols-ospf-ti-frr)# no strict-spf-protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
