protocols mpls traffic-engineering pcep capability association
--------------------------------------------------------------

**Minimum user role:** operator

Once enabled, DNOS as a PCC utilizes association capability and supports association TLVs to reflect the relations between the LSPs.
An example case is the Path Protection Association (per RFC 8745) to express the relation between Primary LSP and Secondary LSP of the same Tunnel.
To set Association capability:

**Command syntax: capability association [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Note**

- The association is only advertised when there is a need to reflect relations between LSPs. I.E if no Secondary LSP is required, even if the capability association is enabled, it is not advertised for the Primary LSP.

- no command returns the capability association to the default state.

**Parameter table**

+-------------+-------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                 | Range        | Default  |
+=============+=============================================================+==============+==========+
| admin-state | When enabled, PCC will utilize association tlvs per RFC8697 | | enabled    | disabled |
|             |                                                             | | disabled   |          |
+-------------+-------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# mpls
    dnRouter(cfg-protocols-mpls)# traffic-engineering
    dnRouter(cfg-protocols-mpls-te)# pcep
    dnRouter(cfg-mpls-te-pcep)# capability association enabled


**Removing Configuration**

To return the admin-state to the default value:
::

    dnRouter(cfg-mpls-te-pcep)# no capability association

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
