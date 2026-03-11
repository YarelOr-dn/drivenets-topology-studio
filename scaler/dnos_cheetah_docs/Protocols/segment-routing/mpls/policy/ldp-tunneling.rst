protocols segment-routing mpls policy ldp-tunneling
---------------------------------------------------

**Minimum user role:** operator

Enables the SR-TE policy to be used for ldp over SR-TE tunneling.
Once enabled, a targeted hello will be initiated to the policy destination to establish a remote ldp session.
An LDP binding will be possible when removing the neighbor with an mpls path that is resolved via the SR-TE policy


**Command syntax: ldp-tunneling [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Configure usage of SR policy for LDP over SR-TE forwarding resolution (LDP       | | enabled    | disabled |
|             | tunneling)                                                                       | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR-POLICY_1
    dnRouter(cfg-sr-mpls-policy)# ldp-tunneling enabeld


**Removing Configuration**

To revert the ldp-tunneling to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no ldp-tunneling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
