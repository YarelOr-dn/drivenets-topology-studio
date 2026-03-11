protocols segment-routing mpls auto-policy template color no-fallback
---------------------------------------------------------------------

**Minimum user role:** operator

Once no-fallback is enabled for an auto-policy template, if all the policy paths associated with the policies created by the template are found to be invalid, leaving the SR-TE with no policy solution to install. Then SR-TE will install a policy to null0 (drop) to the RIB.
As a result there will be no fallback in the RIB for resolving traffic on a different route, if the policy is the best match for both destination and color.

To enable no-fallback:

**Command syntax: no-fallback [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

**Note**
- While creating an auto policy, even with the no-fallback option set, in the interim period until such policy is created, DNOS will attempt to resolve over mpls-nh algo0.

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# no-fallback enabled


**Removing Configuration**

To revert the no-fallback to its default value:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no no-fallback

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
