protocols rsvp tunnel bypass primary cspf-calculation
-----------------------------------------------------

**Minimum user role:** operator

RSVP uses the Constrained Shortest Path First (CSPF) algorithm to calculate traffic paths subject to the administrative-groups, bandwidth requirements, and explicit route objects (EROs) constraints, maintained in the traffic engineering database. In determining which path to select, CSPF uses the Dijkstra algorithm.

When enabled, CSPF calculates the available bandwidth ratio along each valid candidate tunnel path (where a valid candidate tunnel path is an equal cost shortest path that satisfies the path constraints). The available bandwidth ratio is calculated as: available-bandwidth/max-reservable-bandwidth across all path links.

Use the equal-cost mode to define how the available bandwidth ratio is considered for path selection:

- Least-fill - the path with the highest available-bandwidth-ratio is selected

- Most-fill - the path with the lowest available-bandwidth-ratio is selected

- Random - randomly selects a path from all valid path candidates

To enable/disable the CSPF calculation:

**Command syntax: cspf-calculation [cspf-calculation]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass primary

**Note**
- max-reservable-bandwidth is the configured traffic-engineering class-type 0 bandwidth for the TE interface.

.. -  default values for primary tunnels - as global cspf-calculation value
..
.. -  default values for bypass tunnels - enabled with equal-cost "least-fill"
..
.. -  'no cspf-calculation enabled equal-cost' return equal-cost to default value
..
.. -  'no cspf-calculation' command returns cspf-calculation & equal-cost to default values

**Parameter table**

+------------------+------------------------------------------------------------------------------+------------+---------+
| Parameter        | Description                                                                  | Range      | Default |
+==================+==============================================================================+============+=========+
| cspf-calculation | Set whether Constraint Shortest Path Forwarding is used for path calculation | enabled    | \-      |
|                  |                                                                              | disabled   |         |
+------------------+------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# cspf-calculation disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# cspf-calculation enabled equal-cost most-fill

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# cspf-calculation enabled equal-cost random

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# cspf-calculation disabled


**Removing Configuration**

To revert equal-cost to default mode:
::

    dnRouter(cfg-protocols-rsvp-tunnel-primary)# no cspf-calculation enabled equal-cost

To revert cspf-calculation and equal-cost mode to their default values:
::

    dnRouter(cfg-protocols-rsvp-tunnel-primary)# no cspf-calculation

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 9.0     | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 10.0    | Changed the default admin-state value to the global configuration.   |
|         | Added support for manual bypass tunnels.                             |
+---------+----------------------------------------------------------------------+
| 11.0    | Added support for equal-cost mode configuration                      |
+---------+----------------------------------------------------------------------+
