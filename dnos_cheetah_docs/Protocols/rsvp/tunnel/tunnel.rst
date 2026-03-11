protocols rsvp tunnel
---------------------

**Minimum user role:** operator

An RSVP tunnel is a label-switched path (LSP) that can carry inside other RSVP LSPs in order to provide network end-to-end traffic engineering. There are several types of RSVP tunnels, each with its own set of possible configuration and default configuration values. These are:

- RSVP tunnel - a primary LSP that is created immediately upon configuration. See "rsvp tunnel primary".

- Manual bypass tunnel - a backup LSP used for fast reroute protection. The tunnel is created the moment it is attached to an RSVP interface. See "rsvp tunnel bypass".

- Auto-bypass tunnel - an automatically generated LSP profile. The tunnel is created the moment that a protection request arrives from a primary RSVP tunnel. See "rsvp auto-bypass".

- Auto-mesh tunnel - a primary LSP whose configuration and attributes are taken from a tunnel template. The tunnel is created when a new router is discovered in the TE topology database.

The following global RSVP default configurations do not apply for manual and auto-bypass tunnels:

- source-address
- cspf-calculation
- priority
- admin-group

Follow these general steps to create a new tunnel:

1.	Create a new tunnel and give it a name (see below)

2.	Optional. Enter a description for the tunnel (see "rsvp tunnel description").

3.	Enter a destination address for the tunnel (see "rsvp tunnel destination-address").

4.	Optional. Enter the source address of the tunnel (see "rsvp tunnel source-address").

5.	Configure primary tunnel parameters (see "rsvp tunnel primary").

To create a tunnel and enter its configuration mode:

**Command syntax: tunnel [tunnel]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. -  a tunnel name cannot start with "auto\_tunnel'_"

.. -  a tunnel name cannot start with "tunnel\_bypass\_"

.. -  a tunnel name cannot include spaces

.. -  A tunnel is unique by its name, for all bypass and regular tunnels

**Parameter table**

+-----------+-------------+------------------+---------+
| Parameter | Description | Range            | Default |
+===========+=============+==================+=========+
| tunnel    | tunnel name | | string         | \-      |
|           |             | | length 1-255   |         |
+-----------+-------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)#


**Removing Configuration**

To delete the tunnel:
::

    dnRouter(cfg-protocols-rsvp)# no tunnel TUNNEL1

**Command History**

+---------+--------------------------------------------------------+
| Release | Modification                                           |
+=========+========================================================+
| 9.0     | Command introduced                                     |
+---------+--------------------------------------------------------+
| 11.0    | Added restrictions on names                            |
+---------+--------------------------------------------------------+
| 15.0    | Added support for ldp-tunneling and ldp-shortcuts-sync |
+---------+--------------------------------------------------------+
| 15.1    | Added support for primary path-selection               |
+---------+--------------------------------------------------------+
