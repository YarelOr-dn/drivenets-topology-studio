protocols rsvp bfd tail multiplier
----------------------------------

**Minimum user role:** operator

You can set a multiplier to determine the BFD detection timeout over the head end. The timeout calculation is:

Timeout = tail_multiplier x negotiated_tail_tx

To configure a BFD multiplier value for a tunnel tail end:

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols rsvp bfd tail

**Note**
- The new configuration of the BFD multiplier affects only new LSPs established at the tail end.

- The timeout will be 5 times the negotiated tail transmission time.

**Parameter table**

+------------+--------------------------+-------+---------+
| Parameter  | Description              | Range | Default |
+============+==========================+=======+=========+
| multiplier | set local BFD multiplier | 2-16  | 3       |
+------------+--------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# bfd
    dnRouter(cfg-protocols-rsvp-bfd)# tail
    dnRouter(cfg-protocols-rsvp-bfd-tail)# multiplier 5


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-bfd)# no tail multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
