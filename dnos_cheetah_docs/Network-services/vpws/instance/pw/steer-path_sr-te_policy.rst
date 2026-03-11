network-services vpws instance pw steer-path sr-te policy
---------------------------------------------------------

**Minimum user role:** operator

Enable the PW transport resolution over a specific SR-TE policy. When set, the given SR-TE policy is the preferred transport resolution for the given PW of the given service.

**Command syntax: steer-path sr-te policy [sr-te-policy]** no-fallback

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Note**

- When changing between the usage of the SR-TE policy a disabling steer-path usage is expcted to not effect the PW state. Once used, the PW solution will be updated if the policy is up. Once removed, the PW solution will be updated per the best mpls-nh solution.

**Parameter table**

+--------------+-----------------------------------------------------------------------+------------------+---------+
| Parameter    | Description                                                           | Range            | Default |
+==============+=======================================================================+==================+=========+
| sr-te-policy | Enable PW transport resolution over a specific SR-TE policy           | | string         | \-      |
|              |                                                                       | | length 1-255   |         |
+--------------+-----------------------------------------------------------------------+------------------+---------+
| no-fallback  | When specified, prevent fallback next-hop solution over mpls-nh table | boolean          | \-      |
+--------------+-----------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# steer-path sr-te policy SR_TE_POLICY_1

    dnRouter(cfg-network-services-vpws)# instance VPWS_2
    dnRouter(cfg-network-services-vpws-inst)# pw 2.2.2.2
    dnRouter(cfg-vpws-inst-pw)# steer-path sr-te policy SR_TE_POLICY_1 no-fallback


**Removing Configuration**

To remove steer-path usage:
::

    dnRouter(cfg-vpws-inst-pw)# no steer-path

To remove no-fallback action:
::

    dnRouter(cfg-vpws-inst-pw)# no steer-path sr-te policy SR_TE_POLICY_1 no-fallback

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
