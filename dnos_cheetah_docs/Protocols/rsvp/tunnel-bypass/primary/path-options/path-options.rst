protocols rsvp tunnel bypass primary path-options
-------------------------------------------------

**Minimum user role:** operator

Path-options provides a set of constraints for establishing the tunnel. When it is not possible to establish the tunnel with one set of constraints, you can opt to establish it using the next set of constraints (according to priority). After the tunnel is established with a specific path-options, the LSP will use the constraints of the best path option that was successfully established.

By default, the system dynamically computes the tunnel's path using global tunnel attributes.

To configure the path-options and enter path-options configuration mode:

**Command syntax: path-options [path-option]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass primary
- protocols rsvp tunnel primary
- protocols rsvp tunnel secondary
- protocols rsvp auto-mesh tunnel-template primary

**Note**
.. -  default system behavior is to dynamically compute tunnel path using global tunnel attributes
..
.. -  when configuring a better path-option then one currently in use, invoke MBB starting fromt the best path-option. top to bottom. If a worst Path-Option was configured - do .. nothing
..
.. -  the path priority determines which path is examined first, the path is set by the first path that was successfully build
..
.. -  'no path-options [priority]' - remove specific path-option enty
..
.. -  'no path-options' - remove all path-option , returning to system default path option behavior

**Parameter table**

+-------------+----------------------+-------+---------+
| Parameter   | Description          | Range | Default |
+=============+======================+=======+=========+
| path-option | path option priority | 1-10  | \-      |
+-------------+----------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary
    dnRouter(cfg-rsvp-tunnel-primary)# path-options 1
    dnRouter(cfg-tunnel-primary-path-options)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# path-options 5
    dnRouter(cfg-bypass-tunnel-primary-path-options)#


**Removing Configuration**

To remove a specific path-option:
::

    dnRouter(cfg-rsvp-tunnel-primary)# no path-options 1

**Command History**

+---------+-----------------------------------------+
| Release | Modification                            |
+=========+=========================================+
| 9.0     | Command introduced                      |
+---------+-----------------------------------------+
| 10.0    | Added support for manual bypass tunnels |
+---------+-----------------------------------------+
| 11.0    | Updated the priority range              |
+---------+-----------------------------------------+
