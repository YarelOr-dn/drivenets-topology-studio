protocols rsvp tunnel bypass bfd min-tx
---------------------------------------

**Minimum user role:** operator

To set minimum transmit interval for BFD session:

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass bfd

**Note**
- Configuring the BFD parameter will trigger LSP make-before-break to comply with new BFD state.

- Due to hardware limitation, the maximum supported transmit rate is 1700 msec. A negotiated transmit interval higher than 1700 msec will result in an actual transmit rate of 1700 msec.

**Parameter table**

+-----------+-------------------------------------------------------+---------+---------+
| Parameter | Description                                           | Range   | Default |
+===========+=======================================================+=========+=========+
| min-tx    | Set desired minimum transmit interval for BFD session | 50..1700| 300     |
+-----------+-------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# bfd
    dnRouter(cfg-rsvp-tunnel-bfd)# min-tx 350

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# bfd
    dnRouter(cfg-rsvp-bypass-tunnel-bfd)# min-tx 350

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# bfd
    dnRouter(cfg-rsvp-auto-bypass-bfd)# min-tx 350


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no min-tx

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
