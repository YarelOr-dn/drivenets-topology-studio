protocols rsvp explicit-path index ipv4-address
-----------------------------------------------

**Minimum user role:** operator

You can configure explicit paths with include-loose or include-strict:

- Include-strict: identifies an exact path through which the LSP must be routed. Strict-hop explicit paths specify the exact order of routers through which the RSVP messages are sent.

- Include-loose: identifies one or more transit LSRs through which the LSP must be routed. The network IGP (IS-IS) determines the exact route from the head-end router to the first loose hop, or from one loose hop to the next. The loose hop specifies only that a particular LSR be included in the LSP.

- Exclude: identifies one or more LSRs through which the LSP must not be routed.

If you configure explicit an path with include-loose and include-strict simultaneously, the IGP determines the route between loose hops, while the strict-hop configuration specifies the exact path for specific path segments. To configure the explicit path:

**Command syntax: index [explicit-path-index] ipv4-address [ipv4-address]**

**Command mode:** config

**Hierarchies**

- protocols rsvp explicit-path

**Note**
-  If you do not specify an include-strict, include-loose, or exclude, include-strict will be assumed for the specified IP address.

.. -  user can set loopback address as the ipv4-address, in which case

   -  cspf must be enabled in order to resolve the rechability for the loopback address

   -  having "include-strict" for a loopback address will be treated as a loose constraint with requirement of a single hop reachability. E.g if two consecutive address are loopbacks with include-strict, the path may variant between using different links connecting to two nodes.

.. -  no command removes the path entry

**Parameter table**

+---------------------+----------------+---------+---------+
| Parameter           | Description    | Range   | Default |
+=====================+================+=========+=========+
| explicit-path-index | node index     | 1-32    | \-      |
+---------------------+----------------+---------+---------+
| ipv4-address        | lsr-ip-address | A.B.C.D | \-      |
+---------------------+----------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)
    dnRouter(cfg-protocols-rsvp)# explicit-path PATH_1
    dnRouter(cfg-protocols-rsvp-expl-path)# index 1 ipv4-address 192.168.3.2 include-strict
    dnRouter(cfg-protocols-rsvp-expl-path)# index 2 ipv4-address 192.168.3.3 include-strict
    dnRouter(cfg-protocols-rsvp-expl-path)# index 3 ipv4-address 192.168.3.4 include-loose
    dnRouter(cfg-protocols-rsvp-expl-path)# index 4 ipv4-address 192.168.3.5 exclude


    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)
    dnRouter(cfg-protocols-rsvp)# explicit-path PATH_2
    dnRouter(cfg-protocols-rsvp-expl-path)# index 1 ipv4-address 12.122.94.57 exclude
    dnRouter(cfg-protocols-rsvp-expl-path)# index 2 ipv4-address 192.168.3.2 include-strict

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)
    dnRouter(cfg-protocols-rsvp)# explicit-path PATH_3
    dnRouter(cfg-protocols-rsvp-expl-path)# index 1 ipv4-address 192.168.3.2
    dnRouter(cfg-protocols-rsvp-expl-path)# index 2 ipv4-address 192.168.3.3


**Removing Configuration**

To remove a path entry from the explicit path:
::

    dnRouter(cfg-protocols-rsvp-expl-path)# no index 2

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 9.0     | Command introduced                     |
+---------+----------------------------------------+
| 10.0    | Added exclude option to command syntax |
+---------+----------------------------------------+
