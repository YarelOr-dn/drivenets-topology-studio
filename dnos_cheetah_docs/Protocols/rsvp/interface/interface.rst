protocols rsvp interface
------------------------

**Minimum user role:** operator

RSVP signaling is automatically enabled for every MPLS Traffic Engineering enabled interface. In RSVP interface configuration mode, you can configure interface specific behaviors such as RSVP timer and protection.
When an MPLS-TE interface is configured, it is also automatically configured under the rsvp interface hierarchy. You may change the default configuration per interface within the rsvp interface hierarchy.
To enter RSVP interface configuration mode to support RSVP signaling:

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  whenever a mpls traffic-engineering interface is configured, if it does not exist under "protocols rsvp interfaces" the interface will be automatically configured for "protocols rsvp interface".

- Removing an MPLS-TE interface does not result in the removal of the rsvp interface and vice versa.

.. -  no commands remove the interface from rsvp

**Parameter table**

+-----------+----------------+------------------+---------+
| Parameter | Description    | Range            | Default |
+===========+================+==================+=========+
| interface | interface name | | string         | \-      |
|           |                | | length 1-255   |         |
+-----------+----------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# interface bundle-1
    dnRouter(cfg-protocols-rsvp-if)#


**Removing Configuration**

To remove the interface specific configuration:
::

    dnRouter(cfg-protocols-rsvp)# no interface bundle-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
