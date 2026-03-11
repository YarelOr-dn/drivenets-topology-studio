services mpls-oam profile exp
-----------------------------

**Minimum user role:** operator


You can configure the EXP value that will be set in the EXP field of the topmost label. All inner layers will also be set with the matching CoS value, including IP Precedence field of the IPv4 header. This setting will override any global CoS configuration.

To configure the EXP value for MPLS-OAM echo requests:

**Command syntax: exp [exp]**

**Command mode:** config

**Hierarchies**

- services mpls-oam profile

**Parameter table**

+-----------+-----------------------------------------------------------------+-------+---------+
| Parameter | Description                                                     | Range | Default |
+===========+=================================================================+=======+=========+
| exp       | mpls echo request packet class-of-service, set in the exp field | 0-7   | 0       |
+-----------+-----------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# exp 1


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-mpls-oam-profile)# no exp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
