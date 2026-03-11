network-services vpws instance pw steer-path rsvp-te
----------------------------------------------------

**Minimum user role:** operator

Enable PW transport resolution over a specific RSVP-TE tunnel. When set, the given RSVP-TE tunnel is the preferred transport resolution for the given PW of the given service.

**Command syntax: steer-path rsvp-te [rsvp-te]** no-fallback

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Note**

- When changing between the usage of RSVP-TE a disabling steer-path usage is expcted to not effect the PW state. Once used, the PW solution will be updated if the policy is up. Once removed, the PW solution will be updated per best mpls-nh solution.

**Parameter table**

+-------------+-----------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                           | Range            | Default |
+=============+=======================================================================+==================+=========+
| rsvp-te     | resolve by specific rsvp-te tunnel according to tunnel name           | | string         | \-      |
|             |                                                                       | | length 1-255   |         |
+-------------+-----------------------------------------------------------------------+------------------+---------+
| no-fallback | When specified, prevent fallback next-hop solution over mpls-nh table | boolean          | \-      |
+-------------+-----------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# steer-path rsvp-te TUNNEL_1

    dnRouter(cfg-network-services-vpws)# instance VPWS_2
    dnRouter(cfg-network-services-vpws-inst)# pw 2.2.2.2
    dnRouter(cfg-vpws-inst-pw)# steer-path rsvp-te TUNNEL_2 no-fallback


**Removing Configuration**

To remove steer-path usage:
::

    dnRouter(cfg-vpws-inst-pw)# no steer-path

To remove no-fallback action:
::

    dnRouter(cfg-vpws-inst-pw)# no steer-path rsvp-te TUNNEL_2 no-fallback

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
