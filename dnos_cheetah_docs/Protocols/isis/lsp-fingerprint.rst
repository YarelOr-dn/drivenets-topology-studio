protocols isis lsp-fingerprint
------------------------------

**Minimum user role:** operator

Enable advertisement of fingerprint TLV (Type 15) according to rfc8196.
Fingerprint TLV will hold unique system identifiers.
Fingerprint TLV is used to detect duplicating nodes in the network. The detection will result only in a system event, no other corrective action is automatically taken.
To enable LSP fingerprint TLV generation:

**Command syntax: lsp-fingerprint [lsp-fingerprint]**

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- Configuration applies for all ISIS instances and for all levels ISIS is enabled on for a given instance.

- Fingerprint TLV is advertised under the LSP first fragment.

- Fingerprint TLV is advertised with S, A flags unset. Support of fingerprint TLV does not reflect system support for autoconfiguration.

- The system event will comply with DNOS syslog suppression, such as a single syslog notification that is sent every 30sec as long as duplication is recognized by repeatedly getting the conflicting LSP.

- The fingerprint will not be signaled in any other type of packet, but LSP.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter       | Description                                                                      | Range        | Default  |
+=================+==================================================================================+==============+==========+
| lsp-fingerprint | Enable advertisement of fingerprint tlv (Type 15) according to rfc8196.          | | enabled    | disabled |
|                 | Fingerprint tlv will hold system unique identifier. Fingerprint tlv is used to   | | disabled   |          |
|                 | detect duplicating nodes in the network                                          |              |          |
+-----------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# lsp-fingerprint enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-isis)# no lsp-fingerprint

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
