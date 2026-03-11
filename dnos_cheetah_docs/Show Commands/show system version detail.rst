show system version detail
--------------------------

**Minimum user role:** viewer

To display the system version including all firmware components per physical node or for all nodes in the cluster:



**Command syntax: show system version detail** type [type] [node-name] [node-id]

**Command mode:** operational



**Note**

- The version is displayed in the following format: W.X.Y, followed by build number Z, where:

	- W - major version

	- X - minor version

	- Y - BugFix version

	- Z - Build number

- If the node is not configured or connected, no firmware information will be displayed.

.. - show system version describes DNOS deployed cluster version including all firmware components.

	- If node is not configured nor connected, fw information will not be shown.

**Parameter table**

+-----------+------------------------------------------------------+-------------------------+
| Parameter |                      Description                     |          Range          |
+===========+======================================================+=========================+
| type      | Filters the displayed information by component type  | - host-os               |
|           |                                                      |                         |
|           |                                                      | - bios                  |
|           |                                                      |                         |
|           |                                                      | - ipmi                  |
|           |                                                      |                         |
|           |                                                      | - sps                   |
|           |                                                      |                         |
|           |                                                      | - ie                    |
|           |                                                      |                         |
|           |                                                      | - eth-controller        |
|           |                                                      |                         |
|           |                                                      | - pcie-switch           |
|           |                                                      |                         |
|           |                                                      | - pcie-packet-processor |
|           |                                                      |                         |
|           |                                                      | - cpld                  |
|           |                                                      |                         |
|           |                                                      | - ucd                   |
|           |                                                      |                         |
|           |                                                      | - re-timer              |
|           |                                                      |                         |
|           |                                                      | - gearbox               |
|           |                                                      |                         |
|           |                                                      | - clock                 |
|           |                                                      |                         |
|           |                                                      | - onie                  |
+-----------+------------------------------------------------------+-------------------------+
| node-name | Filters the displayed information to a specific node | - NCP                   |
|           |                                                      | - NCF                   |
|           |                                                      | - NCC                   |
|           |                                                      | - NCM                   |
+-----------+------------------------------------------------------+-------------------------+
| node-id   | Filters the displayed information to a specific node | - NCP: 0..249           |
|           |                                                      | - NCF: 0..611           |
|           |                                                      | - NCC: 0..1             |
|           |                                                      | - NCM: A0, A1, B0, B1   |
+-----------+------------------------------------------------------+-------------------------+

**Example**
::

	dnRouter# show system version detail

	System Name: dnRouter
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

	| Node | ID    | Type                  | Component name      | Version                    |
	|------+-------+-----------------------+---------------------+----------------------------|
	| NCP  | 0     | Host-OS               |                     | DriveNets BaseOS 1.443     |
	| NCP  | 0     | BIOS                  |                     | 3.10                       |
	| NCP  | 0     | IPMI                  | Image 1             | 0.5.1                      |
	| NCP  | 0     | IPMI                  | Image 2             | 0.5.1                      |
	| NCP  | 0     | Eth-Controller        | NIC-1 (ctrl-0)      | 16.25.1020                 |
	| NCP  | 0     | Eth-Controller        | NIC-2 (ctrl-1)      | 16.25.1020                 |
	| NCP  | 0     | Eth-Controller        | NIC-3 (ipmi)        | 2.27.9                     |
	| NCP  | 0     | PCIe-Switch           |                     | 1.0                        |
	| NCP  | 0     | PCIe-Packet-Processor | BCM88690            | 2.5                        |
	| NCP  | 0     | CPLD                  | CPU CPLD            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD1            | 0.38                       |
	| NCP  | 0     | CPLD                  | MB CPLD2            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD3            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD4            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD5            | 0.18                       |
	| NCP  | 0     | UCD                   | TOP-MB              | 0.18                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-1          | D00A                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-2          | D00A                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-3          | D00A                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-4          | D00A                       |
	| NCP  | 0     | Gearbox               | Gearbox-1           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-2           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-3           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-4           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-5           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-6           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-7           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-8           | D029                       |
	| NCP  | 0     | ONIE                  |                     | ssl_gdnor-201906040619v06  |
	| NCP  | 0     | Clock                 | PTP Service         | 0.32                       |
	| NCP  | 0     | Clock                 | PTP Protocol stack  | 1.23                       |
	| NCP  | 0     | Clock                 | PTP servo           | 1.23                       |
	| NCP  | 0     | Clock                 | RPC server          | 1.23                       |
	| NCP  | 0     | Clock                 | RPC client          | 1.23                       |
	| NCP  | 0     | Clock                 | CPLD Firmware       | 1.23                       |
	| NCP  | 0     | Clock                 | FPGA Firmware       | 1.23                       |
	| NCP  | 0     | Clock                 | BroadSync Firmware  | 4.3.16.0                   |
	| NCP  | 0     | Clock                 | DPLL model and FW   | ZL30795, 0x07DA            |
	| NCC  | 0     | Host-OS               |                     | DriveNets BaseOS 1.443     |
	| NCC  | 0     | BIOS                  |                     | 3.10                       |
	| NCC  | 0     | IPMI                  | iLO                 | 2.10                       |
	| NCC  | 0     | IE                    |                     | 0.2.2.0                    |
	| NCC  | 0     | SPS                   |                     | 4.1.4.339                  |
	| NCC  | 0     | ONIE                  |                     | ssl_gdnor-201906040619v06  |
	| NCF  | 0     | Host-OS               |                     | DriveNets BaseOS 1.443     |
	| NCF  | 0     | BIOS                  |                     | 3.10                       |
	| NCF  | 0     | IPMI                  | Image 1             | 0.5.1                      |
	| NCF  | 0     | IPMI                  | Image 2             | 0.5.1                      |
	| NCF  | 0     | Eth-Controller        | NIC-1 (ctrl-0)      | 16.25.1020                 |
	| NCF  | 0     | Eth-Controller        | NIC-2 (ctrl-1)      | 16.25.1020                 |
	| NCF  | 0     | Eth-Controller        | NIC-3 (ipmi)        | 2.27.9                     |
	| NCF  | 0     | PCIe-Switch           |                     | 1.0                        |
	| NCF  | 0     | PCIe-Packet-Processor | BCM88790-1          | 2.5                        |
	| NCF  | 0     | PCIe-Packet-Processor | BCM88790-2          | 2.5                        |
	| NCF  | 0     | CPLD                  | CPU CPLD            | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD1            | 0.38                       |
	| NCF  | 0     | CPLD                  | MB CPLD2            | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD3            | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD4            | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD5            | 0.18                       |
	| NCF  | 0     | UCD                   | TOP-MB              | 0.18                       |
	| NCF  | 0     | UCD                   | BOT-MB              | 0.18                       |
	| NCF  | 0     | Re-Timer              | Re-Timer-1          | D00A                       |
	| NCF  | 0     | Re-Timer              | Re-Timer-2          | D00A                       |
	| NCF  | 0     | Re-Timer              | Re-Timer-3          | D00A                       |
	| NCF  | 0     | Re-Timer              | Re-Timer-4          | D00A                       |
	| NCF  | 0     | ONIE                  |                     | ssl_gdnor-201906040619v06  |
	| NCM  | A0    | Host-OS               |                     | DNOS-NCM 1.0.13            |
	| NCM  | A0    | BIOS                  |                     | 3.10                       |
	| NCM  | A0    | IPMI                  | Image 1             | 0.5.1                      |
	| NCM  | A0    | CPLD                  | CPU CPLD            | 0.18                       |
	| NCM  | A0    | CPLD                  | FAN CPLD            | 0.38                       |
	| NCM  | A0    | CPLD                  | MB CPLD1            | 0.18                       |
	| NCM  | A0    | CPLD                  | MB CPLD2            | 0.18                       |
	| NCM  | A0    | ONIE                  |                     | 2018.11.00.01              |


	dnRouter# show system version detail ncp 0

	System Name: dnRouter
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

	| Node | ID    | Type                  | Component name      | Version                    |
	|------+-------+-----------------------+---------------------+----------------------------|
	| NCP  | 0     | Host-OS               |                     | DriveNets BaseOS 1.443     |
	| NCP  | 0     | BIOS                  |                     | 3.10                       |
	| NCP  | 0     | IPMI                  | Image 1             | 0.5.1                      |
	| NCP  | 0     | IPMI                  | Image 2             | 0.5.1                      |
	| NCP  | 0     | Eth-Controller        | NIC-1 (ctrl-0)      | 16.25.1020                 |
	| NCP  | 0     | Eth-Controller        | NIC-2 (ctrl-1)      | 16.25.1020                 |
	| NCP  | 0     | Eth-Controller        | NIC-3 (ipmi)        | 2.27.9                     |
	| NCP  | 0     | PCIe-Switch           |                     | 1.0                        |
	| NCP  | 0     | PCIe-Packet-Processor | BCM88690            | 2.5                        |
	| NCP  | 0     | CPLD                  | CPU CPLD            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD1            | 0.38                       |
	| NCP  | 0     | CPLD                  | MB CPLD2            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD3            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD4            | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD5            | 0.18                       |
	| NCP  | 0     | UCD                   | TOP-MB              | 0.18                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-1          | D00A                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-2          | D00A                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-3          | D00A                       |
	| NCP  | 0     | Re-Timer              | Re-Timer-4          | D00A                       |
	| NCP  | 0     | Gearbox               | Gearbox-1           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-2           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-3           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-4           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-5           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-6           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-7           | D029                       |
	| NCP  | 0     | Gearbox               | Gearbox-8           | D029                       |
	| NCP  | 0     | ONIE                  |                     | ssl_gdnor-201906040619v06  |
	| NCP  | 0     | Clock                 | PTP Service         | 0.32                       |
	| NCP  | 0     | Clock                 | PTP Protocol stack  | 1.23                       |
	| NCP  | 0     | Clock                 | PTP servo           | 1.23                       |
	| NCP  | 0     | Clock                 | RPC server          | 1.23                       |
	| NCP  | 0     | Clock                 | RPC client          | 1.23                       |
	| NCP  | 0     | Clock                 | CPLD Firmware       | 1.23                       |
	| NCP  | 0     | Clock                 | FPGA Firmware       | 1.23                       |
	| NCP  | 0     | Clock                 | BroadSync Firmware  | 4.3.16.0                   |
	| NCP  | 0     | Clock                 | DPLL model and FW   | ZL30795, 0x07DA            |


	dnRouter# show system version detail type bios

	System Name: dnRouter
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

	| Node | ID    | Type                  | Component name   | Version                    |
	|------+-------+-----------------------+------------------+----------------------------|
	| NCC  | 0     | BIOS                  |                  | 3.10                       |
	| NCC  | 1     | BIOS                  |                  | 3.10                       |
	| NCP  | 0     | BIOS                  |                  | 3.10                       |
	| NCP  | 1     | BIOS                  |                  | 3.10                       |
	| NCF  | 0     | BIOS                  |                  | 3.10                       |
	| NCM  | A0    | BIOS                  |                  | 3.10                       |


	dnRouter# show system version detail type bios ncp 0

	System Name: dnRouter
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

	| Node | ID | Type                  | Component name   | Version                    |
	|------+----+-----------------------+------------------+----------------------------|
	| NCP  | 1  | BIOS                  |                  | 3.10                       |


	dnRouter# show system version detail type cpld

	System Name: dnRouter
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

	| Node | ID    | Type                  | Component name   | Version                    |
	|------+-------+-----------------------+------------------+----------------------------|
	| NCP  | 0     | CPLD                  | CPU CPLD         | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD1         | 0.38                       |
	| NCP  | 0     | CPLD                  | MB CPLD2         | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD3         | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD4         | 0.18                       |
	| NCP  | 0     | CPLD                  | MB CPLD5         | 0.18                       |
	| NCF  | 0     | CPLD                  | CPU CPLD         | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD1         | 0.38                       |
	| NCF  | 0     | CPLD                  | MB CPLD2         | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD3         | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD4         | 0.18                       |
	| NCF  | 0     | CPLD                  | MB CPLD5         | 0.18                       |
	| NCM  | A0    | CPLD                  | CPU CPLD         | 0.18                       |
	| NCM  | A0    | CPLD                  | FAN CPLD         | 0.38                       |
	| NCM  | A0    | CPLD                  | MB CPLD1         | 0.18                       |
	| NCM  | A0    | CPLD                  | MB CPLD2         | 0.18                       |


	dnRouter# show system version detail type onie

	System Name: dnRouter
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.

	| Node | ID    | Type                  | Component name   | Version                    |
	|------+-------+-----------------------+------------------+----------------------------|
	| NCP  | 0     | ONIE                  |                  | ssl_gdnor-201906040619v06  |
	| NCC  | 0     | ONIE                  |                  | ssl_gdnor-201906040619v06  |
	| NCF  | 0     | ONIE                  |                  | ssl_gdnor-201906040619v06  |
	| NCM  | A0    | ONIE                  |                  | 2018.11.00.01              |

.. **Help line:** show system version detailed information

**Command History**

+---------+------------------------------------------------------------------------------+
| Release | Modification                                                                 |
+=========+==============================================================================+
| 11.5    | Command introduced, added module name information for PCIe packet processors |
+---------+------------------------------------------------------------------------------+
| 17.2    | Split the build number from the DNOS version                                 |
+---------+------------------------------------------------------------------------------+
