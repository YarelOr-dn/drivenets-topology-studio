system in-band-management dnor-server-vrf
-----------------------------------------

**Minimum user role:** operator

Configures the VRF over which the communication towards DNOR servers will go through.

**Command syntax: system in-band-management dnor-server-vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system in-band-management

**Note:**

-  mgmt0 and default VRFs are the default config, mgmt0 is not configurable and enabled by default. default VRF is configurble and can be updated using this command.
-  The destination as were configured by set mgmt dnor-server command.
-  Validation: the source-interface shall be configured under the VRF, as part of network-services vrf instance in-band-management source-interface CLI command.

**Parameter table:**

+----------------------+---------------------------------------------+---------------+
| Parameter            | Values                                      | Default value |
+======================+=============================================+===============+
| vrf-name             | default          (in-band)                  | default       |
|                      | non-default-vrf  (in-band)                  |               |
+----------------------+---------------------------------------------+---------------+

**CLI example:**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# in-band-management dnor-server-vrf non-default-vrf


**Help line:** Configure DNOR servers VRF.

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
| 19.1        | Command introduced                           |
+-------------+----------------------------------------------+
