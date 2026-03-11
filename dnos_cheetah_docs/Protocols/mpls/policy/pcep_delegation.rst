protocols segment-routing mpls policy pcep delegation
-----------------------------------------------------

**Minimum user role:** operator

Enable SR-TE delegation to a remote PCE.
For a delegated policy, the local router (acting as PCC) will comply with policy updates provided by the PCE.
A policy path provided by PCE will be considered as the most preferred path

Policy information is passed to PCE even if not delegated to it

**Command syntax: pcep delegation [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-------------+------------------------------------------------+------------+---------+
| Parameter   | Description                                    | Range      | Default |
+=============+================================================+============+=========+
| admin-state | Enable SR-TE policy delegation to a remote PCE | enabled    | \-      |
|             |                                                | disabled   |         |
+-------------+------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# pcep delegation enabeld


**Removing Configuration**

To revert the pcep delegation to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no pcep delegation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
