protocols rsvp tunnel secondary bfd min-rx
------------------------------------------

**Minimum user role:** operator

The desired minimum received interval is the time-frame in which a BFD packet is expected to arrive. If a BFD packet is not received within the configured interval, the BFD session will go down.
The min-rx together with the multiplier, defines the detection time.
The Local Detection timeout = negotiated Rx interval * remote_multiplier (the multiplier value received on the BFD packet).
The Remote Detection timeout = negotiated Tx interval * local_multiplier (the multiplier value configured locally for the session).
Set the desired minimum receive interval for the BFD session:


**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary bfd

**Note**

- Due to a hardware limitation, the maximum supported transmit rate is 1700 msec, and a negotiated transmit interval that is higher than 1700 msec will result in an actual transmit rate of 1700 msec.

**Parameter table**

+-----------+---------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                         | Range   | Default |
+===========+=====================================================================+=========+=========+
| min-rx    | The interval (in msec) in which a BFD packet is expected to arrive. | 50-1700 | 1000    |
+-----------+---------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# bfd
    dnRouter(cfg-tunnel-secondary-bfd)# min-rx 50


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-tunnel-secondary-bfd)# no min-rx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
