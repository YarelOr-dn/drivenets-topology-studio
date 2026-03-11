network-services vrf instance protocols bgp address-family ipv6-unicast rib-install policy
------------------------------------------------------------------------------------------

**Minimum user role:** operator

Apply policy on BGP installation to RIB to impose route modifications

**Command syntax: rib-install policy [policy-name]** [, policy-name, policy-name]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- A BGP attribute modification done via policy will not be reflected in the advertised routes to peers. i.e policy is towards rib only and after adj-out construction.

- Policy cannot be used to filter routes from RIB - If policy resulted in deny, e.g matched on a deny rule (or ended on the default deny all rule) policy will not impose any action (including any set actions) on the routes.

- Applies for both unicast and label-unicast routes.

- Policy modification may cause BGP route update to RIB.

- Can set multiple policies. In case multiple policies are set policies are evaluated one after the other according to user input order.

**Parameter table**

+-------------+-----------------------------------------------------+------------------+---------+
| Parameter   | Description                                         | Range            | Default |
+=============+=====================================================+==================+=========+
| policy-name | Policy for routes updated prior to RIB installation | | string         | \-      |
|             |                                                     | | length 1-255   |         |
+-------------+-----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# rib-install policy TO_RIB_POL, TO_RIB_POL2
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# rib-install policy TO_RIB_POL, TO_RIB_POL2


**Removing Configuration**

To remove policy attachment:
::

    dnRouter(cfg-protocols-bgp-afi)# no rib-install policy

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 17.1    | Command introduced                              |
+---------+-------------------------------------------------+
| 17.2    | Added support for multiple policies attachments |
+---------+-------------------------------------------------+
