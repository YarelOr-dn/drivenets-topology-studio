protocols rsvp tunnel secondary bfd min-tx
------------------------------------------

**Minimum user role:** operator

The minimum transmission interval is the time between consecutive transmissions of BFD packets. To configure the transmission rate of BFD packets:


**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary bfd

**Note**

- Due to a hardware limitation, the maximum supported transmit rate is 1700msec, and a negotiated transmit interval that is higher than 1700 msec will result in an actual transmit rate of 1700 msec.

**Parameter table**

+-----------+--------------------------------------------------------------+---------+---------+
| Parameter | Description                                                  | Range   | Default |
+===========+==============================================================+=========+=========+
| min-tx    | The interval (in msec) between transmissions of BFD packets. | 50-1700 | 1000    |
+-----------+--------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# bfd
    dnRouter(cfg-tunnel-secondary-bfd)# min-tx 50


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-tunnel-secondary-bfd)# no min-tx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
