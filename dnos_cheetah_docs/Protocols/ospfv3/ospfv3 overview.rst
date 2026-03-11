Open Shortest Path First (OSPFv3) Overview
------------------------------------------

Open Shortest Path First (OSPFv3) is a link-state routing protocol that operates within a single autonomous system. Each OSPF router maintains an identical database describing the routers' topology. Each router communicates its topology to other routers using link state advertisements (LSA). A topology of the area is constructed from these LSAs and is stored in the database. From this database, each router constructs a tree of shortest paths with itself as a root, giving the route to each destination in the autonomous system. OSPF recalculates routes quickly and dynamically in the face of topological changes, utilizing a minimum of routing protocol traffic.

The OSPF protocol is enabled with equal-cost multi-path routing (ECMP) so that packet forwarding to a single destination can spread across multiple next-hops as opposed to a single “best”.

The following commands are common to OSPFv2 (IPv4 OSPF version) and OSPFv3 (IPv6 OSPF version).

The following table maps the commands available per OSPF version:

+-------------------------------------------------------+------+--------+
| Command                                               | OSPF | OSPFv3 |
+-------------------------------------------------------+------+--------+
| clear ospf statistics                                 | +    | +      |
+-------------------------------------------------------+------+--------+
| clear ospf routes                                     | +    | +      |
+-------------------------------------------------------+------+--------+
| clear ospf process                                    | +    | +      |
+-------------------------------------------------------+------+--------+
| clear ospf database                                   | +    | +      |
+-------------------------------------------------------+------+--------+
| clear ospf interfaces                                 | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface hello-interval                    | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf auto-cost reference-bandwidth                    | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf class-of-service                                 | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf default-originate                                | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area bfd admin-state                             | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area bfd min-rx                                  | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area bfd min-tx                                  | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area bfd multiplier                              | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area bfd                                         | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf max-metric router-lsa-administrative             | +    |        |
+-------------------------------------------------------+------+--------+
| ospf max-metric router-lsa on-startup                 | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd                               | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd admin-state                   | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd min-rx                        | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd min-tx                        | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface bfd multiplier                    | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf maximum-ecmp-paths                               | +    |        |
+-------------------------------------------------------+------+--------+
| ospf maximum-redistributed-prefixes                   | +    |        |
+-------------------------------------------------------+------+--------+
| ospf redistribute                                     | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf redistribute-metric                              | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf timers refresh                                   | +    |        |
+-------------------------------------------------------+------+--------+
| ospf timers throttle lsa all                          | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf timers lsa-arrival                               | +    |        |
+-------------------------------------------------------+------+--------+
| ospf timers throttle spf                              | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf administrative distance                          | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface cost                              | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface dead-interval                     | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface mtu-ignore                        | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface network                           | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface passive                           | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area interface                                   | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf area                                             | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf log-adjacency-changes                            | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf router-id                                        | +    | +      |
+-------------------------------------------------------+------+--------+
| protocols ospf                                        | +    | +      |
+-------------------------------------------------------+------+--------+
| ospf mpls ldp-sync                                    | +    |        |
+-------------------------------------------------------+------+--------+
| ospf graceful-restart                                 | +    |        |
+-------------------------------------------------------+------+--------+
| ospf fast-reroute                                     | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area network                                     | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area authentication                              | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area filter-list in/out                          | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication                    | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication-key authentication | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface authentication-key md5            | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface fast-reroute-candidate            | +    |        |
+-------------------------------------------------------+------+--------+
| ospf area interface cost-mirroring                    | +    |        |
+-------------------------------------------------------+------+--------+
