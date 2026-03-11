protocols rsvp tunnel bypass primary equal-cost
-----------------------------------------------

**Minimum user role:** operator

RSVP uses the Constrained Shortest Path First (CSPF) algorithm to calculate traffic paths that are subject to the following constraints:

- LSP attributes - Administrative groups such as link coloring, bandwidth requirements, and EROs

- Link attributes - Colors on a particular link and available bandwidth

These constraints are maintained in the traffic engineering database. The database provides CSPF with up-to-date topology information, the current reservable bandwidth of links, and the link colors. You can configure whether or not CSPF is used for path calculation. When disabled, the tunnel path must be explicitly set in order for the tunnel to be established. When enabled, CSPF calculates the available bandwidth ratio along each valid candidate tunnel path (where a valid candidate tunnel path is an equal cost shortest path that satisfies the path constraints). The available bandwidth ratio is calculated as: available-bandwidth/max-reservable-bandwidth across all path links.  
Use the equal-cost mode to define how the available bandwidth ratio is considered for path selection:

- Least-fill - the path with the highest available-bandwidth-ratio is selected

- Most-fill - the path with the lowest available-bandwidth-ratio is selected

- Random - randomly selects a path from all valid path candidates

To enable/disable CSPF path calculation:

**Command syntax: equal-cost [equal-cost]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass primary
- protocols rsvp tunnel primary
- protocols rsvp auto-mesh tunnel-template primary

**Note**
-  max-reservable-bandwidth is the configured traffic-engineering class-type 0 bandwidth for the TE interface.

.. -  'no equal-cost enabled equal-cost' return equal-cost to default value

.. -  'no equal-cost' command returns equal-cost & equal-cost to default values

**Parameter table**

+------------+-----------------------------------------------------------------------+----------------+---------+
| Parameter  | Description                                                           | Range          | Default |
+============+=======================================================================+================+=========+
| equal-cost | choose how available-bandwidth-ratio is considered for path selection | | least-fill   | \-      |
|            |                                                                       | | most-fill    |         |
|            |                                                                       | | random       |         |
+------------+-----------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# equal-cost disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# equal-cost enabled equal-cost random


**Removing Configuration**

To revert equal-cost to default mode:
::

    dnRouter(cfg-protocols-rsvp)# no equal-cost enabled equal-cost

To revert equal-cost and equal-cost mode to their default values:
::

    dnRouter(cfg-protocols-rsvp)# no equal-cost

**Command History**

+---------+---------------------------------------------------------------+
| Release | Modification                                                  |
+=========+===============================================================+
| 10.0    | Command introduced                                            |
+---------+---------------------------------------------------------------+
| 11.0    | Added "most-fill" and "random" selection of equal cost paths. |
+---------+---------------------------------------------------------------+
