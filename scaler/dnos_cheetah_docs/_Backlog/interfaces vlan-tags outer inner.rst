interfaces vlan-tags outer inner -N/A for this version
------------------------------------------------------

**Command syntax: vlan-tags outer [outer-vlan-id] inner [inner-vlan-id]**

**Description:** configure sub interface qinq (double tagged vlan)

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1.2
	dnRouter(cfg-if-bundle-1.2)# vlan-tags outer 20 inner 20

	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1.3
	dnRouter(cfg-if-bundle-1.3)# vlan-tags outer 20 inner 30

	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1.4
	dnRouter(cfg-if-bundle-1.4)# vlan-tags outer 20 inner 40

	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# ge10-1/1/2.100
	dnRouter(cfg-if-ge10-1/1/2.100)# vlan-tags outer 20 inner 301


	dnRouter(cfg-if)# no bundle-1.2
	dnRouter(cfg-if)# no ge10-1/1/2.100

**Command mode:** config

**TACACS role:** operator

**Note:**

vlan-tags command is available only for sub-interface/bundle.sub-interface

vlan-tags command is not available for physical/loopback interfaces

vlan-tags is a must parameter for qinq sub-interface

vlan-tags and vlan-id are mutually exclusive

Sub-interface is created when using the interface.sub-interface-id syntax

Vlan-tags command configured the sub-interface with qinq encapsulation.

To preserve sub-interface properties, it is possible to change its type from qinq to vlan without removing the sub-interface configuration

Outer TPID value is 0x88a8. Inner TPID value is 0x8100.

no command removes the sub-interface configuration

**Help line:** Configure interface qinq vlan-tags

**Parameter table:**

+------------------+---------------------------------+---------------+
| Parameter        | Values                          | Default value |
+==================+=================================+===============+
| interface-name   | ge<interface speed>-<A>/<B>/<C> |               |
|                  |                                 |               |
|                  | bundle-<bundle id>              |               |
+------------------+---------------------------------+---------------+
| Sub-interface-id | 1-65535                         |               |
+------------------+---------------------------------+---------------+
| outer-vlan-id    | 1-4094                          |               |
+------------------+---------------------------------+---------------+
| inner-vlan-id    | 1-4094                          |               |
+------------------+---------------------------------+---------------+
