protocols rsvp source-address
-----------------------------

**Minimum user role:** operator

To configure the RSVP IP source address to be used in tunnel signaling:

**Command syntax: source-address [source-address]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+----------------+------------------------------------------------------+---------+---------+
| Parameter      | Description                                          | Range   | Default |
+================+======================================================+=========+=========+
| source-address | rsvp ip source address to be use in tunnel signaling | A.B.C.D | \-      |
+----------------+------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# source-address 10.10.10.10


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no source-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
