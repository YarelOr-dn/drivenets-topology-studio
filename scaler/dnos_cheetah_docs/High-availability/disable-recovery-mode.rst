system high-availability disable-recovery-mode
----------------------------------------------

**Command syntax: disable-recovery-mode**

**Description:** Configure whether or not system should enter recovery-mode. Once set, recovery mode is disabled in the system.
System will avoid recovery mode, resulting in NCC restart.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# disable-recovery-mode

	dnRouter(cfg-system-ha)# no disable-recovery-mode

**Command mode:** config

**TACACS role:** operator

**Note:**


-  no command remove 'disable-recovery-mode' settings and return system to allow entering recovery-mode


**Help line:** Disable recovery-mode usage in system

