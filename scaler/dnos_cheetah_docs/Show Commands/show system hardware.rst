show system hardware
--------------------

**Minimum user role:** viewer

To display hardware information, use the following command:



**Command syntax: show system hardware** [node-name] [node-id]

**Command mode:** operational



**Note**

- In a standalone setup, show system hardware and show system hardware [node-name] [node-id] display the same information.


.. for usb output:

	- vendor id can be reached via lsusb -v -> idVendor

	- Descriptor Type -> bDescriptorType

	- Device Class -> bDeviceClass

**Parameter table**

+-----------+-------------------------------------------------+---------------------+
| Parameter | Description                                     | Range               |
+===========+=================================================+=====================+
| node-name | The name of the node depicting its function.    | NCP, NCF, NCC, NCM  |
+-----------+-------------------------------------------------+---------------------+
| node-id   | The identifier for the node.                    | NCP: 0..249         |
|           |                                                 | NCC: 0..1           |
|           |                                                 | NCF: 0..611         |
|           |                                                 | NCM: A0-1, B0-1     |
+-----------+-------------------------------------------------+---------------------+
| Uptime    | The amount of time the hardware was in Up state | dddd days, hh:mm:ss |
+-----------+-------------------------------------------------+---------------------+

**Example**

In the following example, the hardware information is displayed for each node in the cluster:


::

	dnRouter# show system hardware
	System Name: dnRouter

	ncc 0 (dn-ncc-0)
	Model: X86
	Hardware Model: ProLiant DL380 Gen10
	Hardware Revision: N/A
	Serial Number: ABCDE1001
	Host Name: ABCDE1001
	Host Operating System: DriveNets BaseOS 1.443
	ONIE Version: ssl_gdnor-201906040619v06
	Manufacturer: HPE

	Hardware Information:
	  | Item          | Value                                          |
	  |---------------+------------------------------------------------|
	  | Cores         | 8                                              |
	  | CPU [MHz]     | Current: 2200.160875, Min: 800.0, Max: 2200.0  |
	  | CPU Model     | Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz          |
	  | Hyper-Threads | 16 (2 per Core)                                |

	CPU Usage:
	  | CPU           | Use % |
	  |---------------+-------|
	  | CPU0          | 70.0  |
	  | CPU1          | 70.9  |
	  | CPU2          | 100.0 |
	  | CPU3          | 99.9  |
	  | CPU4          | 71.0  |
	  | CPU5          | 72.0  |
	  | CPU6          | 73.0  |
	  | CPU7          | 74.0  |

	  Last 1 minute CPU load average: 80%
	  Last 5 minutes CPU load average: 70%

	Memory Usage:
	  | Type                | Total | Used | Free | Shared | Buffers | Cached |
	  |---------------------|-------+------+------+--------+---------+--------+
	  | Physical            | 31G   | 16G  | 14G  | 203M   | 1.6M    | 1.5G   |
	  | Swap                | 4.0G  | 0B   | 4.0G |        |         |        |

	Disk Information:

	  | Item                  | Disk1                | Disk2                |
	  |-----------------------+----------------------|----------------------|
	  | Physical location     | 1I:3:1               | 1I:3:2               |
	  | Capacity              | 480GB                | 480GB                |
	  | Model                 | MK000480GWTTH        | MK000480GWTTH        |
	  | Firmware revision     | 4IYRHPG1             | 4IYRHPG1             |
	  | Serial Number         | BTYG91050EA8480BGN   | BTYG91050FEF480BGN   |
	  | Health status         | OK                   | WARNING              |
	  | Lifetime Utilization  | 19%                  | 92%                  |
	  | kB Written/s          | 3530.61              | 3162.32              |

	 Disk Usage:
	  | File System         | Size  | Used  | Avail | Use % | Mounted on       |
	  |---------------------+-------+-------+-------+-------+------------------|
	  | udev                | 1.2G  | 4.0K  | 1.2G  | 1%    | /dev             |
	  | tmpfs               | 3.2G  | 11M   | 3.2G  | 1%    | /run             |
	  | /dev/dm-0           | 21G   | 6.5G  | 15G   | 32%   | /                |
	  | none                | 4.0K  | 0     | 4.0K  | 0%    | /sys/fs/cgroup   |
	  | none                | 5.0M  | 0     | 5.0M  | 0%    | /run/lock        |
	  | none                | 16G   | 194M  | 16G   | 2%    | /run/shm         |
	  | none                | 100M  | 0     | 100M  | 0%    | /run/user        |
	  | /dev/vda1           | 236   | 93M   | 131M  | 42%   | /boot            |

	BIOS Version:
	  2.22

	BIOS Mode:
	  Legacy

	IPMI version:
	  | Module Name      | Image 1 Version | Image 2 Version |
	  |------------------+-----------------+-----------------|
	  | BMC              | iLo 5 v2.10     | N/A             |

	Innovation Engine (IE) Version:
	  0.2.2.0

	Server Platform Service (SPS) Version:
	  4.1.4.339

	On-board Management Ethernet Controller Version:
	  | NIC              | Version         | Description                                     |
	  |------------------+-----------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | 16.25.1020      | Mellanox 100G Ethernet Controller               |
	  | 2 (ctrl-1)       | 16.25.1020      | Mellanox 100G Ethernet Controller               |

	Power Supply Units:
	  Redundancy mode: 1+1
	  | PSU ID | Present   | Status       | Serial         | Revision  | Type         | Uptime             |
	  |--------+-----------+--------------+----------------+-----------+--------------|--------------------|
	  | 0      | YES       | OK           | 5WBXU0DLLBM3XA | 1.0       | AC 100-240 V |  30 days, 04:35:06 |
	  | 1      | YES       | OK           | 5WBXU0DLLBM3H4 | 1.0       | AC 100-240 V |  30 days, 04:35:06 |

	Temperature Sensors:
	  | Sensor Name      | Temperature [C] | Status | High Warning | High Critical | Fan 100%           |
	  |                  |                 |        | Threshold [C]| Threshold [C] | User Threshold [C] |
	  |------------------+-----------------+--------+--------------+---------------+--------------------|
	  | 01-Inlet Ambient | 21              | OK     | 42           | 47            | N/A                |
	  | 02-CPU 1         | 40              | OK     | 70           | N/A           | N/A                |
	  | 03-CPU 2         | 40              | OK     | 70           | N/A           | N/A                |
	  | 04-P1 DIMM 1-6   | 30              | OK     | 90           | N/A           | N/A                |
	  | 06-P1 DIMM 7-12  | 27              | OK     | 90           | N/A           | N/A                |
	  | 08-P2 DIMM 1-6   | 36              | OK     | 90           | N/A           | N/A                |
	  | 10-P2 DIMM 7-12  | 32              | OK     | 90           | N/A           | N/A                |
	  | 12-HD Max        | 35              | OK     | 60           | N/A           | N/A                |
	  | 14-Stor Batt 1   | 30              | OK     | 60           | N/A           | N/A                |
	  | 15-Front Ambient | 28              | OK     | 70           | N/A           | N/A                |
	  | 16-VR P1         | 32              | OK     | 115          | 120           | N/A                |
	  | 17-VR P2         | 39              | OK     | 115          | 120           | N/A                |
	  | 18-VR P1 Mem 1   | 26              | OK     | 115          | 120           | N/A                |
	  | 19-VR P1 Mem 2   | 29              | OK     | 115          | 120           | N/A                |
	  | 20-VR P2 Mem 1   | 35              | OK     | 115          | 120           | N/A                |
	  | 21-VR P2 Mem 2   | 35              | OK     | 115          | 120           | N/A                |
	  | 22-Chipset       | 34              | OK     | 100          | N/A           | N/A                |
	  | 23-BMC           | 60              | OK     | 110          | 115           | N/A                |
	  | 24-BMC Zone      | 33              | OK     | 90           | 95            | N/A                |
	  | 25-HD Controller | 54              | OK     | 100          | N/A           | N/A                |
	  | 26-HD Cntlr Zone | 29              | OK     | 85           | 90            | N/A                |
	  | 27-LOM           | 40              | OK     | 100          | N/A           | N/A                |
	  | 29-LOM Card Zone | 29              | OK     | 75           | 80            | N/A                |
	  | 32-PCI 2         | 46              | OK     | 100          | N/A           | N/A                |
	  | 33-PCI 2 Zone    | 27              | OK     | 75           | 80            | N/A                |
	  | 34-PCI 3         | 40              | OK     | 100          | N/A           | N/A                |
	  | 35-PCI 3 Zone    | 29              | OK     | 75           | 80            | N/A                |
	  | 37-PCI 4 Zone    | 30              | OK     | 75           | 80            | N/A                |
	  | 39-PCI 5 Zone    | 31              | OK     | 75           | 80            | N/A                |
	  | 43-PCI 7 Zone    | 33              | OK     | 75           | 80            | N/A                |
	  | 53-Battery Zone  | 32              | OK     | 75           | 80            | N/A                |
	  | 54-P/S 1 Inlet   | 33              | OK     | N/A          | N/A           | N/A                |
	  | 55-P/S 2 Inlet   | 33              | OK     | N/A          | N/A           | N/A                |
	  | 56-P/S 1         | 40              | OK     | N/A          | N/A           | N/A                |
	  | 57-P/S 2         | 40              | OK     | N/A          | N/A           | N/A                |
	  | 58-P/S 2 Zone    | 36              | OK     | 75           | 80            | N/A                |
	  | 59-E-Fuse        | 33              | OK     | 100          | N/A           | N/A                |

	Fans:
	  Redundancy mode: 1+1
	  | Fan ID    | Present   | Status   | Speed [RPM]   | Max RPM   | RPM % | Uptime             |
	  |-----------+-----------+----------+---------------+-----------+-------|--------------------|
	  | Fan 1     | YES       | OK       | N/A           | N/A       | 100   |  30 days, 04:35:06 |
	  | Fan 2     | YES       | OK       | N/A           | N/A       | 100   |   5 days, 20:35:00 |
	  | Fan 3     | YES       | OK       | N/A           | N/A       | 100   |  30 days, 04:35:06 |
	  | Fan 4     | YES       | OK       | N/A           | N/A       | 100   |  30 days, 04:35:06 |
	  | Fan 5     | YES       | OK       | N/A           | N/A       | 100   |  30 days, 04:35:06 |
	  | Fan 6     | YES       | OK       | N/A           | N/A       | 100   |  10 days, 02:01:01 |
	  | PSU 0 Fan | YES       | OK       | N/A           | N/A       | N/A   |  30 days, 04:35:06 |
	  | PSU 1 Fan | YES       | OK       | N/A           | N/A       | N/A   |  10 days, 02:01:01 |


	ncp 0 (dn-ncp-0)
	Model: NCP-40C
	Hardware Model: S9700-53DX (configured: S9700-53DX)
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	Host Name: ABCDE1001
	Host Operating System: DriveNets BaseOS 1.443
	ONIE Version: ssl_gdnor-201906040619v06
	Manufacturer: Ufi Space

	Hardware Information:
	  | Item          | Value                                          |
	  |---------------+------------------------------------------------|
	  | Cores         | 8                                              |
	  | CPU [MHz]     | Current: 2200.160875, Min: 800.0, Max: 2200.0  |
	  | CPU Model     | Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz          |
	  | Hyper-Threads | 16 (2 per Core)                                |

	CPU Usage:
	  | CPU           | Use % |
	  |---------------+-------|
	  | CPU0          | 70.0  |
	  | CPU1          | 70.9  |
	  | CPU2          | 100.0 |
	  | CPU3          | 99.9  |
	  | CPU4          | 71.0  |
	  | CPU5          | 72.0  |
	  | CPU6          | 73.0  |
	  | CPU7          | 74.0  |

	  Last 1 minute CPU load average: 80%
	  Last 5 minutes CPU load average: 70%

	 Memory Usage:
	  | Type                | Total | Used | Free | Shared | Buffers | Cached |
	  |---------------------+-------+------+------+--------+---------+--------+
	  | Physical            | 31G   | 16G  | 14G  | 203M   | 1.6M    | 1.5G   |
	  | Swap                | 4.0G  | 0B   | 4.0G |        |         |        |

	  Channel 0 failure prediction test: FAIL (0 days, 07:23:16)

	Disk Information:
	  | Item                  | Disk1                                         |
	  |-----------------------+-----------------------------------------------|
	  | Physical location     | 1                                             |
	  | Capacity              | 128GB                                         |
	  | Model                 | ATP I-Temp M.2 2280                           |
	  | Firmware revision     | R0822A                                        |
	  | Serial Number         | 99001190924000000053                          |
	  | Health status         | OK                                            |
	  | Lifetime Utilization  | 38%                                           |
	  | kB Written/sec        | 361.03                                        |

	 Disk Usage:
	  | File System         | Size  | Used  | Avail | Use % | Mounted on       |
	  |---------------------+-------+-------+-------+-------+------------------|
	  | udev                | 1.2G  | 4.0K  | 1.2G  | 1%    | /dev             |
	  | tmpfs               | 3.2G  | 11M   | 3.2G  | 1%    | /run             |
	  | /dev/dm-0           | 21G   | 6.5G  | 15G   | 32%   | /                |
	  | none                | 4.0K  | 0     | 4.0K  | 0%    | /sys/fs/cgroup   |
	  | none                | 5.0M  | 0     | 5.0M  | 0%    | /run/lock        |
	  | none                | 16G   | 194M  | 16G   | 2%    | /run/shm         |
	  | none                | 100M  | 0     | 100M  | 0%    | /run/user        |
	  | /dev/vda1           | 236   | 93M   | 131M  | 42%   | /boot            |

	BIOS Version:
	  T77O994T01_R03.10_Apollo

	BIOS Mode:
	  UEFI

	PCIe Switch Version:
	  PEX8724_NCP_v1

	PCIe Packet Processor Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | BCM88690         | 2.5           |

	CPLD Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | CPU CPLD         | 0.15          |
	  | MB CPLD1         | 0.38          |
	  | MB CPLD2         | 0.15          |
	  | MB CPLD3         | 0.15          |
	  | MB CPLD4         | 0.15          |
	  | MB CPLD5         | 0.15          |

	IPMI version:
	  | Module Name      | Image 1 Version | Image 2 Version |
	  |------------------+-----------------+-----------------|
	  | ast2400e         | 0.5.000001      | 0.5.000001      |

	On-board Management Ethernet Controller Version:
	  | NIC              | Version         | Description                                     |
	  |------------------+-----------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 2 (ctrl-1)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 3 (ipmi)         | v2.27.9         | Intel(R) I210 Gigabit Network Connection        |

	Re-Timer Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | Re-Timer-1       | D00A          |
	  | Re-Timer-2       | D00A          |
	  | Re-Timer-3       | D00A          |
	  | Re-Timer-4       | D00A          |

	Gearbox Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | Gearbox-1        | D029          |
	  | Gearbox-2        | D029          |
	  | Gearbox-3        | D029          |
	  | Gearbox-4        | D029          |
	  | Gearbox-5        | D029          |
	  | Gearbox-6        | D029          |
	  | Gearbox-7        | D029          |
	  | Gearbox-8        | D029          |
	  | Gearbox-9        | D029          |
	  | Gearbox-10       | D029          |

    UCD (Power Up Sequence Device) Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | TOP-MB           | v05           |

	USB Ports:
	  Port 0
	   Admin-state: disabled
	   Descriptor Type: 1
	   Device Class: 9 Hub
	   Vendor id: 0x8087 Intel Corp

	Power Supply Units:
	  Redundancy mode: 1+1
	  | PSU ID   | Present   | Status   | Serial              | Revision   | Type    |
	  |----------+-----------+----------+---------------------+------------+---------|
	  | 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | DC 48V  |
	  | 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V |

    Temperature Sensors:
	  | Sensor Name   | Temperature [C] | Status | High Warning | High Critical | Fan 100%           |
	  |               |                 |        | Threshold [C]| Threshold [C] | User Threshold [C] |
	  |---------------+-----------------+--------+--------------+---------------+--------------------|
	  | TEMP_BMC      | 23              | OK     | 60           | 75            | N/A                |
	  | TEMP_BOARD1   | 65              | WARN   | 60           | 75            | N/A                |
	  | TEMP_BOARD2   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_L   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_R   | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_L   | 40              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_R   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_QSFP1    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_QSFP2    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_CPU_PECI | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU1     | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU0     | 38              | OK     | 60           | 75            | N/A                |

	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime             |
	  |----------+---------+--------+-------------+---------+-------|--------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   |  30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   |  30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   |  30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 20000   | 20%   |  30 days, 04:35:06 |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   |  30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                    |

	dnRouter# show system hardware ncp 0
	System Name: dnRouter

	ncp 0 (dn-ncp-0)
	Model: NCP-40C
	Hardware Model: S9700-53DX (configured: S9700-53DX)
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	Host Name: ABCDE1001
	Host Operating System: DriveNets BaseOS 1.443
	ONIE Version: ssl_gdnor-201906040619v06
	Manufacturer: Ufi Space

	Hardware Information:
	  | Item          | Value                                          |
	  |---------------+------------------------------------------------|
	  | Cores         | 8                                              |
	  | CPU [MHz]     | Current: 2200.160875, Min: 800.0, Max: 2200.0  |
	  | CPU Model     | Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz          |
	  | Hyper-Threads | 16 (2 per Core)                                |

	CPU Usage:
	  | CPU           | Use % |
	  |---------------+-------|
	  | CPU0          | 70.0  |
	  | CPU1          | 70.9  |
	  | CPU2          | 100.0 |
	  | CPU3          | 99.9  |
	  | CPU4          | 71.0  |
	  | CPU5          | 72.0  |
	  | CPU6          | 73.0  |
	  | CPU7          | 74.0  |

	  Last 1 minute CPU load average: 80%
	  Last 5 minutes CPU load average: 70%

	 Memory Usage:
	  | Type                | Total | Used | Free | Shared | Buffers | Cached |
	  |---------------------+-------+------+------+--------+---------+--------+
	  | Physical            | 31G   | 16G  | 14G  | 203M   | 1.6M    | 1.5G   |
	  | Swap                | 4.0G  | 0B   | 4.0G |        |         |        |

	  Channel 0 failure prediction test: PASS (0 days, 01:44:21)

	Disk Information:
	  | Item                  | Disk1                                         |
	  |-----------------------+-----------------------------------------------|
	  | Physical location     | 1                                             |
	  | Capacity              | 128GB                                         |
	  | Model                 | ATP I-Temp M.2 2280                           |
	  | Firmware revision     | R0822A                                        |
	  | Serial Number         | 99001190924000000053                          |
	  | Health status         | WARNING                                       |
	  | Lifetime Utilization  | 91%                                           |
	  | kB Written/sec        | 361.51                                        |

	 Disk Usage:
	  | File System         | Size  | Used  | Avail | Use % | Mounted on       |
	  |---------------------+-------+-------+-------+-------+------------------|
	  | udev                | 1.2G  | 4.0K  | 1.2G  | 1%    | /dev             |
	  | tmpfs               | 3.2G  | 11M   | 3.2G  | 1%    | /run             |
	  | /dev/dm-0           | 21G   | 6.5G  | 15G   | 32%   | /                |
	  | none                | 4.0K  | 0     | 4.0K  | 0%    | /sys/fs/cgroup   |
	  | none                | 5.0M  | 0     | 5.0M  | 0%    | /run/lock        |
	  | none                | 16G   | 194M  | 16G   | 2%    | /run/shm         |
	  | none                | 100M  | 0     | 100M  | 0%    | /run/user        |
	  | /dev/vda1           | 236   | 93M   | 131M  | 42%   | /boot            |

	BIOS Version:
	  T77O994T01_R03.10_Apollo

	BIOS Mode:
	  UEFI

	PCIe Switch Version:
	  PEX8724_NCP_v1

	PCIe Packet Processor Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | BCM88690         | 2.5           |

	CPLD Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | CPU CPLD         | 0.15          |
	  | MB CPLD1         | 0.38          |
	  | MB CPLD2         | 0.15          |
	  | MB CPLD3         | 0.15          |
	  | MB CPLD4         | 0.15          |
	  | MB CPLD5         | 0.15          |

	IPMI version:
	  | Module Name      | Image 1 Version | Image 2 Version |
	  |------------------+-----------------+-----------------|
	  | ast2400e         | 0.5.000001      | 0.5.000001      |

	On-board Management Ethernet Controller Version:
	  | NIC              | Version         | Description                                     |
	  |------------------+-----------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 2 (ctrl-1)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 3 (ipmi)         | v2.27.9         | Intel(R) I210 Gigabit Network Connection        |

	Re-Timer Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | Re-Timer-1       | D00A          |
	  | Re-Timer-2       | D00A          |
	  | Re-Timer-3       | D00A          |
	  | Re-Timer-4       | D00A          |

	Gearbox Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | Gearbox-1        | D029          |
	  | Gearbox-2        | D029          |
	  | Gearbox-3        | D029          |
	  | Gearbox-4        | D029          |
	  | Gearbox-5        | D029          |
	  | Gearbox-6        | D029          |
	  | Gearbox-7        | D029          |
	  | Gearbox-8        | D029          |
	  | Gearbox-9        | D029          |
	  | Gearbox-10       | D029          |

    UCD (Power Up Sequence Device) Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | TOP-MB           | v05           |

	USB Ports:
	  Port 0
	   Admin-state: disabled
	   Descriptor Type: 1
	   Device Class: 9 Hub
	   Vendor id: 0x8087 Intel Corp

	Power Supply Units:
	  Redundancy mode: 1+1
	  | PSU ID   | Present   | Status   | Serial              | Revision   | Type    | Uptime            |
	  |----------+-----------+----------+---------------------+------------+---------|-------------------|
	  | 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | DC 48V  |                   |
	  | 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V | 30 days, 04:35:06 |

    Temperature Sensors:
	  | Sensor Name   | Temperature [C] | Status | High Warning | High Critical | Fan 100%           |
	  |               |                 |        | Threshold [C]| Threshold [C] | User Threshold [C] |
	  |---------------+-----------------+--------+--------------+---------------+--------------------|
	  | TEMP_BMC      | 23              | OK     | 60           | 75            | N/A                |
	  | TEMP_BMC      | 23              | OK     | 60           | 75            | N/A                |
	  | TEMP_BOARD1   | 65              | WARN   | 60           | 75            | N/A                |
	  | TEMP_BOARD2   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_L   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_R   | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_L   | 40              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_R   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_QSFP1    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_QSFP2    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_CPU_PECI | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU1     | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU0     | 38              | OK     | 60           | 75            | N/A                |

	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime            |
	  |----------+---------+--------+-------------+---------+-------|-------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   | 30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   | 30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   | 30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 20000   | 20%   | 30 days, 04:35:06 |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   | 30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                   |

	dnRouter# show system hardware ncf 0
	System Name: dnRouter

	ncf 0 (dn-ncf-0)
	Model: NCF-48CD
	Hardware Model: S9705-48D
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDE1001
	Host Name: ABCDE1001
	Host Operating System: DriveNets BaseOS 1.443
	ONIE Version: ssl_gdnor-201906040619v06
	Manufacturer: Ufi Space

	Hardware Information:
	  | Item          | Value                                          |
	  |---------------+------------------------------------------------|
	  | Cores         | 8                                              |
	  | CPU [MHz]     | Current: 2200.160875, Min: 800.0, Max: 2200.0  |
	  | CPU Model     | Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz          |
	  | Hyper-Threads | 16 (2 per Core)                                |

	CPU Usage:
	  | CPU           | Use % |
	  |---------------+-------|
	  | CPU0          | 70.0  |
	  | CPU1          | 70.9  |
	  | CPU2          | 100.0 |
	  | CPU3          | 99.9  |
	  | CPU4          | 71.0  |
	  | CPU5          | 72.0  |
	  | CPU6          | 73.0  |
	  | CPU7          | 74.0  |

	  Last 1 minute CPU load average: 80%
	  Last 5 minutes CPU load average: 70%

	 Memory Usage:
	  | Type                | Total | Used | Free | Shared | Buffers | Cached |
	  |---------------------+-------+------+------+--------+---------+--------+
	  | Physical            | 31G   | 16G  | 14G  | 203M   | 1.6M    | 1.5G   |
	  | Swap                | 4.0G  | 0B   | 4.0G |        |         |        |

	  Channel 0 failure prediction test: PASS (0 days, 11:04:12)

	Disk Information:
	  | Item                  | Disk1                                         |
	  |-----------------------+-----------------------------------------------|
	  | Physical location     | 1                                             |
	  | Capacity              | 128GB                                         |
	  | Model                 | ATP I-Temp M.2 2280                           |
	  | Firmware revision     | R0822A                                        |
	  | Serial Number         | 99001190924000000053                          |
	  | Health status         | FAIL                                          |
	  | Lifetime Utilization  | 25%                                           |
	  | kB Written/sec        | 192.75                                        |

	 Disk Usage:
	  | File System         | Size  | Used  | Avail | Use % | Mounted on       |
	  |---------------------+-------+-------+-------+-------+------------------|
	  | udev                | 1.2G  | 4.0K  | 1.2G  | 1%    | /dev             |
	  | tmpfs               | 3.2G  | 11M   | 3.2G  | 1%    | /run             |
	  | /dev/dm-0           | 21G   | 6.5G  | 15G   | 32%   | /                |
	  | none                | 4.0K  | 0     | 4.0K  | 0%    | /sys/fs/cgroup   |
	  | none                | 5.0M  | 0     | 5.0M  | 0%    | /run/lock        |
	  | none                | 16G   | 194M  | 16G   | 2%    | /run/shm         |
	  | none                | 100M  | 0     | 100M  | 0%    | /run/user        |
	  | /dev/vda1           | 236   | 93M   | 131M  | 42%   | /boot            |

	BIOS Version:
	  T77O994T01_R03.10_Apollo

	BIOS Mode:
	  UEFI

	PCIe Switch Version:
	  PEX8724_NCF_v1

	PCIe Packet Processor Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | BCM88790-1       | 2.5           |
	  | BCM88790-2       | 2.5           |

	CPLD Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | CPU CPLD         | 0.15          |
	  | MB CPLD1         | 0.38          |
	  | MB CPLD2         | 0.15          |
	  | MB CPLD3         | 0.15          |
	  | MB CPLD4         | 0.15          |
	  | MB CPLD5         | 0.15          |

	IPMI version:
	  | Module Name      | Image 1 Version | Image 2 Version |
	  |------------------+-----------------+-----------------|
	  | ast2400e         | 0.5.000001      | 0.5.000001      |

	On-board Management Ethernet Controller Version:
	  | NIC              | Version         | Description                                     |
	  |------------------+-----------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 2 (ctrl-1)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 3 (ipmi)         | v2.27.9         | Intel(R) I210 Gigabit Network Connection        |

	Re-Timer Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | Re-Timer-1       | D00A          |
	  | Re-Timer-2       | D00A          |
	  | Re-Timer-3       | D00A          |
	  | Re-Timer-4       | D00A          |

    UCD (Power Up Sequence Device) Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | BOT-MB           | v09           |
	  | TOP-MB           | v05           |

	USB Ports:
	  Port 0
	   Admin-state: disabled
	   Descriptor Type: 1
	   Device Class: 9 Hub
	   Vendor id: 0x8087 Intel Corp

	Power Supply Units:
	  Redundancy mode: 1+1
	  | PSU ID   | Present   | Status   | Serial              | Revision   | Type    | Uptime            |
	  |----------+-----------+----------+---------------------+------------+---------|-------------------|
	  | 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | DC 48V  |                   |
	  | 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V | 30 days, 04:35:06 |

	Temperature Sensors:
	  | Sensor Name   | Temperature [C] | Status | High Warning | High Critical | Fan 100%           |
	  |               |                 |        | Threshold [C]| Threshold [C] | User Threshold [C] |
	  |---------------+-----------------+--------+--------------+---------------+--------------------|
	  | TEMP_BMC      | 23              | OK     | 60           | 75            | N/A                |
	  | TEMP_BOARD1   | 65              | WARN   | 60           | 75            | N/A                |
	  | TEMP_BOARD2   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_L   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_R   | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_L   | 40              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_R   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_QSFP1    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_QSFP2    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_CPU_PECI | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU1     | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU0     | 38              | OK     | 60           | 75            | N/A                |

	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime            |
	  |----------+---------+--------+-------------+---------+-------|-------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   | 30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   | 30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   | 30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 20000   | 20%   | 30 days, 04:35:06 |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   | 30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                   |

	dnRouter# show system hardware ncm A0
	System Name: dnRouter

	ncm A0 (dn-ncm-A0)
	Model: NCP48X-6C
	Hardware Model: 5916-54XL-OT-AC-F
	Hardware revision: R03A
	Serial Number: AAF1925AACS
	Host Operating System: DNOS-NCM 1.0.13
	ONIE version: 2018.11.00.01
	Manufacturer: Edgecore

	CPU Usage:
	  | CPU           | Use % |
	  |---------------|-------|
	  | TOTAL         | 70.0  |

	  Last 1 minute CPU load average: 80%
	  Last 5 minutes CPU load average: 70%

	Memory Usage:
	  | Type                | Total | Used | Free | Shared | Buffers | Cached |
	  |---------------------|-------+------+------+--------+---------+--------+
	  | Physical            | 31G   | 16G  | 14G  |  N/A   |   N/A   | 1.5G   |

	Disk Information:
	  | Item                  | Disk1                                         |
	  |-----------------------+-----------------------------------------------|
	  | Physical location     | 1                                             |
	  | Capacity              | 128GB                                         |
	  | Model                 | ATP I-Temp M.2 2280                           |
	  | Firmware revision     | R0822A                                        |
	  | Serial Number         | 99001190924000000053                          |
	  | Health status         | FAIL                                          |
	  | Lifetime Utilization  | 38%                                           |
	  | kB Written/sec        | 406.80                                        |

	BIOS Version:
	  v40.01.00.3

	BIOS Mode:
	  Legacy

	CPLD Version:
	  | Module Name            | Image Version |
	  |------------------------+---------------|
	  | Main CPLD- U64 (CPLD1) | 0xb (11)      |
	  | Main CPLD- U61 (CPLD2) | 0x6 (6)       |
	  | CPU CPLD               | 0x16 (22)     |
	  | FAN CPLD               | 0x03 (3)      |

	IPMI version:
	  | Module Name      | Image 1 Version | Image 2 Version |
	  |------------------+-----------------+-----------------|
	  | BMC              | 0.4b            |                 |

	USB Ports:
	  Port 0
	   Admin-state: disabled
	   Descriptor Type: 1
	   Device Class: 9 Hub
	   Vendor id: 0x8087 Intel Corp

	Power Supply Units:
	  Redundancy mode: 1+1
	  | PSU ID   | Present   | Status   | Serial              | Revision   | Type    | Uptime            |
	  |----------+-----------+----------+---------------------+------------+---------|-------------------|
	  | 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | DC 48V  |                   |
	  | 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V | 30 days, 04:35:06 |

	Temperature Sensors:
	  | Sensor Name            | Temperature [C]   | Status   | High Warning    | High Critical   | Fan 100%           |
	  |                        |                   |          | Threshold [C]   | Threshold [C]   | User Threshold [C] |
	  |------------------------+-------------------+----------+-----------------+-----------------+--------------------|
	  | LM75_1: Main Board U39 | 22.0              | OK       | 55              | 60              | N/A                |
	  | LM75_2: Main Board U50 | 19.0              | OK       | 55              | 60              | N/A                |
	  | LM75_3: Main Board U35 | 24.0              | OK       | 55              | 60              | N/A                |
	  | LM75_4: CPU Board U20  | 21.0              | OK       | 55              | 60              | N/A                |

	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime            |
	  |----------+---------+--------+-------------+---------+-------|-------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   | 30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   | 30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   | 30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 20000   | 20%   | 30 days, 04:35:06 |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   | 30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                   |

	-----------------------------------------------------------------------------------------
	NCP Light SA ncp (note: version numbers, serial numbers and parameter values are only given as example)
	-----------------------------------------------------------------------------------------
	dnRouter# show system hardware ncp 0
	System Name: dnRouter

	ncp 0 (dn-ncp-0)
	Model: NCP-64X12C-S
	Hardware Model: S9701-82DC (configured: S9701-82DC)
	Hardware Revision: 2, Build: 4
	Serial Number: ABCDEFGH
	Host Name: ABCDEFGH
	Host Operating System: DriveNets BaseOS 1.443
	ONIE Version: ssl_gdnor-TBD
	Manufacturer: Ufi Space

	Hardware Information:
	  | Item          | Value                                          |
	  |---------------+------------------------------------------------|
	  | Cores         | 8                                              |
	  | CPU [MHz]     | Current: 1900.160875, Min: 800.0, Max: 3000.0  |
	  | CPU Model     | Intel(R) Xeon(R) CPU D-2145NT @ 1.90GHz        |
	  | Hyper-Threads | 16 (2 per Core)                                |

	CPU Usage:
	  | CPU           | Use % |
	  |---------------+-------|
	  | CPU0          | 70.0  |
	  | CPU1          | 70.9  |
	  | CPU2          | 100.0 |
	  | CPU3          | 99.9  |
	  | CPU4          | 71.0  |
	  | CPU5          | 72.0  |
	  | CPU6          | 73.0  |
	  | CPU7          | 74.0  |
	  | CPU8          | 70.0  |
	  | CPU9          | 70.9  |
	  | CPU10         | 100.0 |
	  | CPU11         | 99.9  |
	  | CPU12         | 71.0  |
	  | CPU13         | 72.0  |
	  | CPU14         | 73.0  |
	  | CPU15         | 74.0  |

	  Last 1 minute CPU load average: 80%
	  Last 5 minutes CPU load average: 70%

	 Memory Usage:
	  | Type                | Total | Used | Free | Shared | Buffers | Cached |
	  |---------------------+-------+------+------+--------+---------+--------+
	  | Physical            | 64G   | 16G  | 48G  | 203M   | 1.6M    | 1.5G   |
	  | Swap                | 4.0G  | 0B   | 4.0G |        |         |        |

	  Channel 0 failure prediction test: PASS (0 days, 01:44:21)
	  Channel 1 failure prediction test: FAIL (0 days, 01:44:21)

	Disk Information:
	  | Item                  | Disk1                                         |
	  |-----------------------+-----------------------------------------------|
	  | Physical location     | 1                                             |
	  | Capacity              | 128GB                                         |
	  | Model                 | ATP I-Temp M.2 2280                           |
	  | Firmware revision     | R0822A                                        |
	  | Serial Number         | 99001190924000000053                          |
	  | Health status         | OK                                            |
	  | Lifetime Utilization  | 38%                                           |
	  | kB Written/sec        | 361.03                                        |

	 Disk Usage:
	  | File System         | Size  | Used  | Avail | Use % | Mounted on       |
	  |---------------------+-------+-------+-------+-------+------------------|
	  | udev                | 1.2G  | 4.0K  | 1.2G  | 1%    | /dev             |
	  | tmpfs               | 3.2G  | 11M   | 3.2G  | 1%    | /run             |
	  | /dev/dm-0           | 21G   | 6.5G  | 15G   | 32%   | /                |
	  | none                | 4.0K  | 0     | 4.0K  | 0%    | /sys/fs/cgroup   |
	  | none                | 5.0M  | 0     | 5.0M  | 0%    | /run/lock        |
	  | none                | 16G   | 194M  | 16G   | 2%    | /run/shm         |
	  | none                | 100M  | 0     | 100M  | 0%    | /run/user        |
	  | /dev/vda1           | 236   | 93M   | 131M  | 42%   | /boot            |

	BIOS Version:
	  TBD

	BIOS Mode:
	  UEFI

	[No PCIe Switch information]

	PCIe Packet Processor Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | BCM88802         | 2.5           |

	CPLD Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | CPU CPLD         | 0.xx          |
	  | MB CPLD1         | 0.ii          |
	  | MB CPLD2         | 0.jj          |
	  | MB CPLD3         | 0.kk          |
	  | MB CPLD4         | 0.ll          |

	IPMI version:
	  | Module Name      | Image 1 Version | Image 2 Version |
	  |------------------+-----------------+-----------------|
	  | ast2400          | 0.5.000001      | 0.5.000001      |

	On-board Management Ethernet Controller Version:
	  | NIC              | Version         | Description                                     |
	  |------------------+-----------------+-------------------------------------------------|
	  | 1 (ctrl-0)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 2 (ctrl-1)       | v2.27.9         | Intel(R) Intel(R) Ethernet Connection X552      |
	  | 3 (ipmi)         | v2.27.9         | Intel(R) I210 Gigabit Network Connection        |

	Gearbox Version:
	  | Module Name      | Image Version |
	  |------------------+---------------|
	  | Gearbox-1        | TBD           |

    Synchronization Management Unit Model:
        ZL30795, 0x07DA

    [No UCD (Power Up Sequence Device) information]

	USB Ports:
	  Port 0
	   Admin-state: disabled
	   Descriptor Type: 1
	   Device Class: 9 Hub
	   Vendor id: 0x8087 Intel Corp

	Power Supply Units:
	  Redundancy mode: 1+1
	  | PSU ID   | Present   | Status   | Serial              | Revision   | Type    |
	  |----------+-----------+----------+---------------------+------------+---------|
	  | 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | DC 48V  |
	  | 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V |

    Temperature Sensors:
	  | Sensor Name   | Temperature [C] | Status | High Warning | High Critical | Fan 100%           |
	  |               |                 |        | Threshold [C]| Threshold [C] | User Threshold [C] |
	  |---------------+-----------------+--------+--------------+---------------+--------------------|
	  | TEMP_BMC      | 23              | OK     | 60           | 75            | N/A                |
	  | TEMP_BOARD1   | 65              | WARN   | 60           | 75            | N/A                |
	  | TEMP_BOARD2   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_L   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_R   | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_L   | 40              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_R   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_CPU_PECI | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU1     | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU0     | 38              | OK     | 60           | 75            | N/A                |

	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime             |
	  |----------+---------+--------+-------------+---------+-------|--------------------|
	  | 1        | YES     | OK     | 9000        | 17710   | XX%   |  30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 17710   | XX%   |  30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 17710   | XX%   |  30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 17710   | XX%   |  30 days, 04:35:06 |
	  | PSU0     | YES     | OK     | 9000        | 17710   | XX%   |  30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                    |

.. **Help line:** show system hardware

**Command History**

+---------+--------------------------------------------------------------------------------+
| Release | Modification                                                                   |
+=========+================================================================================+
| 5.1.0   | Command introduced                                                             |
+---------+--------------------------------------------------------------------------------+
| 10.0    | Updated to the new NCR architecture.                                           |
+---------+--------------------------------------------------------------------------------+
| 11.4    | Added hardware versions                                                        |
+---------+--------------------------------------------------------------------------------+
| 11.5    | Added module name information for PCIe packet processors                       |
+---------+--------------------------------------------------------------------------------+
| 11.6    | Updated BIOS and Fans information                                              |
+---------+--------------------------------------------------------------------------------+
| 13.3    | Added disk information to the command output (applicable to NCC, NCP, and NCF) |
+---------+--------------------------------------------------------------------------------+
| 18.2    | Removed "fabric type" lines                                                    |
+---------+--------------------------------------------------------------------------------+
| 18.2.1  | Added memory failure prediction status                                         |
+---------+--------------------------------------------------------------------------------+
