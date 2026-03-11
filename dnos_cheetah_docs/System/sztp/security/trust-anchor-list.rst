system sztp security trust-anchor-list
--------------------------------------

**Minimum user role:** admin


Configure the list of trust-anchors to authenticate bootstrap-servers in the TLS connection. 

Each item in the list is the name of the certificate chain file that is stored in the /security/cert folder.

To Upload certificate chain file refer to \"request file download\".

The trust-anchor will be used to authenticate the bootsrap-server, unless the bootstrap-server has its own trust-anchor list.

The bootstrap-server is considered authenticated if the certificate chain of the bootstrap-server is signed by one of the trust-anchors in the list.

**Command syntax: trust-anchor-list [trust-anchor-list]** [, trust-anchor-list, trust-anchor-list]

**Command mode:** config

**Hierarchies**

- system sztp security

**Note**

- The user can define for a given bootstrap-server different trust-anchors that will override those trust-anchors defined in the global configuration.

- You can add up to 12 trust-anchors in global configuration.

**Parameter table**

+-------------------+--------------------------------------------------------------------------+-------+---------+
| Parameter         | Description                                                              | Range | Default |
+===================+==========================================================================+=======+=========+
| trust-anchor-list | The filename of trust anchor certificate within the device's file system | \-    | \-      |
+-------------------+--------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter#(cfg) system
    dnRouter#(cfg-sys) sztp
    dnRouter#(cfg-sys-sztp) security
    dnRouter#(cfg-sys-sztp-sec) trust-anchor anchor1
    dnRouter#(cfg-sys-sztp-sec) trust-anchor anchor2


**Removing Configuration**

To revert trust-anchor to default:
::

    dnRouter(cfg-sztp)# no trust-anchor

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
