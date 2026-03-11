protocols segment-routing mpls policy path priority
---------------------------------------------------

**Minimum user role:** operator

Configure path priority


**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy path

**Parameter table**

+-----------+----------------------------+-------+---------+
| Parameter | Description                | Range | Default |
+===========+============================+=======+=========+
| priority  | SR-TE policy path priority | 1-255 | \-      |
+-----------+----------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# path PATH_1
    dnRouter(cfg-mpls-policy-path)# priority 5
    dnRouter(cfg-mpls-policy-path)#


**Removing Configuration**

To remove the priority setting:
::

    dnRouter(cfg-mpls-policy-path)# no priority

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 17.0    | Command introduced                      |
+---------+-----------------------------------------+
| 18.3    | Command detached from base path command |
+---------+-----------------------------------------+
