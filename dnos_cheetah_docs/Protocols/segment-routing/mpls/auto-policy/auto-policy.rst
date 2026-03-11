protocols segment-routing mpls auto-policy
------------------------------------------

**Minimum user role:** operator

Segment Routing auto policies allow a service head-end router to dynamically create an SR-TE policy for a route resolved over BGP next-hop when required (on-demand).
The head-end router automatically follows the actions defined in the template upon arrival of BGP global or VPN routes with a BGP color extended community that matches the color value specified in the template.

Key benefits include:

* SLA-aware BGP service – provides per-destination steering behaviors where a prefix, a set of prefixes, or all prefixes from a service can be associated with a desired underlay SLA. The functionality applies equally to single-domain and multi-domain networks.

* Simplicity – no prior SR Policy configuration needs to be configured and maintained. Instead, operator simply configures a small set of common intent-based optimization templates throughout the network.

* Scalability – device resources at the head-end router are used only when required, based on service or SLA connectivity needs.


To enter segment-routing auto policy configuration hierarchy:

**Command syntax: auto-policy**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)#


**Removing Configuration**

To remove all configured auto-policy templates and revert global configuration to default:
::

    dnRouter(cfg-protocols-sr-mpls)# no auto-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
