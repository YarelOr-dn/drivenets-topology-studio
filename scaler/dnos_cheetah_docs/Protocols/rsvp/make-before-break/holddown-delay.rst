protocols rsvp make-before-break holddown-delay
-----------------------------------------------

**Minimum user role:** operator

You can set a timer for controlling the amount of time following a switchover to a new path in which the old path will be removed. This timer is activated only after the install-delay timer has expired and the tunnel has started forwarding traffic over the new path.
To configure the holddown delay timer:

**Command syntax: holddown-delay [holddown-delay]**

**Command mode:** config

**Hierarchies**

- protocols rsvp make-before-break

**Note**
IPP is set accordingly. i.e DSCP 48 is mapped to 6.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                      | Range   | Default |
+================+==================================================================================+=========+=========+
| holddown-delay | delay the time to remove the old paths following a switchover to the optimized   | 0-65535 | 10      |
|                | path                                                                             |         |         |
+----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# make-before-break
    dnRouter(cfg-protocols-rsvp-mbb)# holddown-delay 10


**Removing Configuration**

To revert to the default holddown-delay:
::

    dnRouter(cfg-protocols-rsvp-mbb)# no holddown-delay

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 9.0     | Command introduced                         |
+---------+--------------------------------------------+
| 10.0    | Changed default value from 20 to 5 seconds |
+---------+--------------------------------------------+
