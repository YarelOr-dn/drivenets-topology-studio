protocols rsvp auto-bypass
--------------------------

**Minimum user role:** operator

An auto-bypass tunnel is an automatically generated LSP profile. The tunnel is created the moment that a protection request arrives from a primary RSVP tunnel. The following are the properties of an auto-bypass tunnel profile:

- It inherently includes a constraint to avoid the interface it bypasses.

- Its source address is the IPv4 address of the interface it protects (non-configurable). This address must differ from the source-address of the primary LSP it protects.

- Its path and destination is according to the LSP it protects (the RRO) and if link or node protection is needed.

- The default parameter values for a manual bypass tunnel are:

  - name - automatically assigned using this format: "tunnel_bypass_<link/node>-<interface>_<ID>"

  - Link/node are set per bypass-tunnel protection type (see "rsvp protection" and "rsvp interface protection")

  - interface - the name of the interface that the tunnel protects

  - ID - a number incremented at tunnel creation

  - bandwidth = 0 mbps

  - exclude-srlg = strict

  - class-type = 0

  - igp-instance - the IGP instance of the interface configured in IGP (e.g. IS-IS)

  - cspf-calculation = enabled, the equal-cost mode is according to the RSVP global cspf-calculation equal-cost settings

  - hop-limit = 255

You can configure admin-group constraints for auto-bypass tunnels, overriding the "requesting" primary LSP constraints.

To enter auto-bypass tunnel configuration mode:

**Command syntax: auto-bypass**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- You cannot remove a manual bypass tunnel if it is attached to an RSVP interface.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)


**Removing Configuration**

To revert all auto-bypass tunnel profile configuration to their default values:
::

    dnRouter(cfg-protocols-rsvp)# no auto-bypass

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
