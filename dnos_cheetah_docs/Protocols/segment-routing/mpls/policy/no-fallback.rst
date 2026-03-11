protocols segment-routing mpls policy no-fallback
-------------------------------------------------

**Minimum user role:** operator

Once no-fallback is enabled for a given policy, if all the policy paths are found to be invalid (including PCE path) leaving the SR-TE with no policy solution to install. The SR-TE will install a policy to null0 (drop) to the RIB. 
As a result there will be no fallback in RIB for resolving traffic on a different route, if the policy is the best match for both destination and color.
To enable no-fallback:


**Command syntax: no-fallback [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-------------+------------------------------------------------------+--------------+----------+
| Parameter   | Description                                          | Range        | Default  |
+=============+======================================================+==============+==========+
| admin-state | Set policy to drop traffic in no valid path is found | | enabled    | disabled |
|             |                                                      | | disabled   |          |
+-------------+------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# no-fallback enabled


**Removing Configuration**

To revert the no-fallback to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no no-fallback

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
