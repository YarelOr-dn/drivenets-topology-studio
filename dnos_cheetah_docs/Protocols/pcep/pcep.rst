protocols segment-routing pcep
------------------------------

**Minimum user role:** operator

A path computation element (PCE) is a network entity that is able to calculate a network path based on the network topology. A path computation client (PCC) is a client application that requests a path computation from the PCE. The path computation element protocol (PCEP) is a TCP-based protocol that enables communication between PCEs and between PCE and PCC.

PCEP defines messages and objects for managing PCEP sessions and for requesting and sending path calculations. This includes SR-TE policy LSP status reports sent by the PCC and updates on external LSPs sent by the PCE.
In PCEP configuration mode, you can optimize network SR-TE policy paths and provide control over PCC defined paths.
By default, all SR-TE policies are reported to the PCE. Delegated policies are also controlled by the PCE

To configure pcep, enter pcep configuration mode:

**Command syntax: pcep**

**Command mode:** config

**Hierarchies**

- protocols segment-routing

**Note**

- PCEP sessions use TCP destination port 4189.

- PCEP supports in-band connectivity only.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)#


**Removing Configuration**

To revert all sr-te pcep configuration to default:
::

    dnRouter(cfg-protocols-sr)# no pcep

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
