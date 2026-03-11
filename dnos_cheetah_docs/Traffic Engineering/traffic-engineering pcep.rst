traffic-engineering pcep
------------------------

**Minimum user role:** operator

A path computation element (PCE) is a network entity that is able to calculate a network path based on the network topology. A path computation client (PCC) is a client application that requests a path computation from the PCE. The path computation element protocol (PCEP) is a TCP-based protocol that enables communication between PCEs and between PCE and PCC.

PCEP defines messages and objects for managing PCEP sessions and for requesting and sending path calculations. This includes LSP status reports sent by the PCC and updates on external LSPs sent by the PCE.
In PCEP configuration mode, you can optimize network LSP traffic-engineering paths and provide control over PCC initiated LSPs. A PCC works in hybrid mode when LSP decisions are taken both locally in the PCC and remotely by the PCE. By default, all tunnels are reported to the PCE. Delegated tunnels are also controlled by the PCE (see "rsvp pcep delegation").

The PCE itself does not establish new tunnels; it controls the following LSP attributes:

-	Bandwidth

-	ERO

-	Priority

-	Admin-group

To enter PCEP configuration hierarchy:

**Command syntax: pcep**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

- PCEP sessions use TCP destination port 4189.

- PCEP supports in-band connectivity only.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep
	dnRouter(cfg-mpls-te-pcep)# 

**Removing Configuration**

To revert PCEP to its default disabled mode and reset all of its configuration:
::

	dnRouter(cfg-protocols-mpls-te)# no pcep


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+