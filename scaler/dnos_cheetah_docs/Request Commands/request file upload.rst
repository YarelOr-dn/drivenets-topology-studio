request file upload
--------------------

**Minimum user role:** operator

Upload file to remote location

**Command syntax: request file upload** { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} **[file-type] [file-name]** [user-name]@ **[destination-file-path] [url]** out-of-band | source-interface [source-interface]

**Command mode:** operational

**Note:**

file upload should provide progress-bar or percentage while uploading (default linux scp should be fine)

source-address [source-address] - set source ip-address for SSH packets. If source-interface is set, the source IP address shall be derived from the set source-interface. Else, source IP address shall be derived from the interface that packet was forwarded from (according to the default VRF routing table)

Each file type has a different location. User cannot upload files from any location other than the predetermined ones (not even if he knows the exact path on the guest os).

If no ncc-id/ncp-id/ncf-id/ncm-id was specified, the command relates to the active NCC

File types locations:

-  config - /config/

-  log - /var/log/dn/

-  traces - /var/log/dn/traces

-  core - /core/

-  tech-support - /techsupport/

-  rollback - /rollback/

-  certificate -  /security/cert/

-  golden-config - /golden_config/

-  event-policy - /event-manager/event-policy/scripts/

-  periodic-policy - /event-manager/periodic-policy/scripts/

-  generic-policy - /event-manager/generic-policy/scripts/

-  packet-capture - /packet-capture/

file types to upload from NCCs:

-  config

-  log

-  traces

-  core

-  certificate

-  golden-config

-  tech-support - possible for active NCC only

-  rollback - possible for active NCC only

-  ssh-keys - possible for active NCC only

-  event-policy - possible for active NCC only

-  periodic-policy - possible for active NCC only

-  generic-policy - possible for active NCC only

-  packet-capture - possible for active NCC only

file types to upload from NCPs/NCFs:

-  log

-  traces

-  core

file types to upload files on NCMs:

-  log

-  config

-  core

-  tech-support

If the requested file does not exist, the following error message will be displayed "Requested file not found"

It is not possible to upload techsupport file from Standby NCC while connected to Active NCC

**Parameter table:**

+-----------------------+--------------------------------------------------------+---------------+
| Parameter             | Values                                                 | Default value |
+=======================+========================================================+===============+
| file-type             | log / config / core / tech-support / rollback / traces |               |
|                       | / ssh-keys                                             |               |
|                       | / certificate / golden-config                          |               |
|                       | / event-policy / periodic-policy                       |               |
|                       | / generic-policy / packet-capture                      |               |
+-----------------------+--------------------------------------------------------+---------------+
| file-name             | string. Including sub-directory (/).                   |               |
+-----------------------+--------------------------------------------------------+---------------+
| destination-file-path | string                                                 |               |
+-----------------------+--------------------------------------------------------+---------------+
| url                   | user@host://destination-filename                       |               |
+-----------------------+--------------------------------------------------------+---------------+
| User-name             | string                                                 | Current user  |
+-----------------------+--------------------------------------------------------+---------------+
| ncc-id                | 0..1                                                   |               |
+-----------------------+--------------------------------------------------------+---------------+
| ncp-id                | 0..249                                                 |               |
+-----------------------+--------------------------------------------------------+---------------+
| ncf-id                | 0-611                                                  |               |
+-----------------------+--------------------------------------------------------+---------------+
| ncm-id                | a0, b0, a1, b1                                         |               |
+-----------------------+--------------------------------------------------------+---------------+
| source-interface      | Any interface in the global VRF with IPv4 address      |               |
|                       | except GRE tunnel interfaces                           |               |
+-----------------------+--------------------------------------------------------+---------------+

**Example**
::

	dnRouter# request file upload tech-support MyTS-14-Jan-2017.tar.gz user@192.168.1.1://MyTS.tar.gz
	File loading ...100%

	dnRouter# request file upload log bgp.log user@192.168.1.1://bgp.log
	File loading ...100%

	dnRouter# request file upload forwarding-engine 1 log cheetah.log user@192.168.1.1://bgp.log
	File loading ...100%

	dnRouter# request file upload core bgpd-core.tar.gz user@192.168.1.1://bgpd-core.tar.gz
	File loading ...100%

	dnRouter# request file upload config MyConfig user@192.168.1.1://MyConfig
	File loading ...100%

	dnRouter# request file upload rollback rollback_5 user@192.168.1.1://rollback_5
	File loading ...100%

	dnRouter# request file upload packet-capture BGP_Debug_.1.pcap
	File loading ...100%

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+

