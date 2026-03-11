protocols segment-routing mpls path
-----------------------------------

**Minimum user role:** operator

A segment-routing path can contain up to 8 segment-lists. Each segment-list defines a path according to the different segments (SIDs) specified for it. Multiple segment-lists within the same path can be used to apply weighted ECMP of traffic forwarding between the different segment-lists.

The path must be valid for a policy to be able to use it.

A path is valid only if all segment-lists with in it are valid. A segment-list is invalid if:

•	The segment-list is empty
•	The head-end is unable to perform path resolution for the first SID into one or more outgoing interface(s) and next-hop(s)
•	The head-end is unable to perform SID resolution for any prefix-SID other than the first into an MPLS label.
•	The SID is known with an R-flag (i.e., is propagated from a different level)
•	The SID appears more than once on the path (loop)
•	Consecutive SIDs belong to the same node.

An empty path, i.e., a path with no segment-list, is also invalid for policy usage.

To configure the segment-routing path and enter its configuration hierarchy:


**Command syntax: path [path]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Note**
Required validations:

- cannot remove a path which is configured for a given sr policy

- path must have at least one segment-list configure.


**Parameter table**

+-----------+---------------------------+------------------+---------+
| Parameter | Description               | Range            | Default |
+===========+===========================+==================+=========+
| path      | segment-routing path name | | string         | \-      |
|           |                           | | length 1-255   |         |
+-----------+---------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)#


**Removing Configuration**

To remove a path or all paths:
::

    dnRouter(cfg-protocols-sr-mpls)# no path PATH_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
