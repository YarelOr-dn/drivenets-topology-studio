protocols rsvp make-before-break
--------------------------------

**Minimum user role:** operator

The NCR operates in make-before-break mode by default. It will never tear down a path before an alternative path is established. When a tunnel is created, the tunnel may perform optimization actions to find a better path. In this case, the old path will remain active until the new path becomes active. You can configure timers to control the time-frames in which the two paths coexist. The following attribute change will cause creating a new LSP in a make-before-break fashion:

- priority

- bandwidth

- exclude-srlg

- admin-group

- path

- igp instance

- cspf-calculation

- explicit-null

To configure the make-before-break timers, enter make-before-break configuration mode:

**Command syntax: make-before-break**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# make-before-break
    dnRouter(cfg-protocols-rsvp-mmb)#


**Removing Configuration**

To revert all make-before-break configuration to the default values:
::

    dnRouter(cfg-protocols-rsvp)# no make-before-break

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
