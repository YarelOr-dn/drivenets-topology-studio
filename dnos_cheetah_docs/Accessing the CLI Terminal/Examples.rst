Examples
--------

**Minimum user role:** operator

The examples in the DNOS command line interface (CLI) are for illustration puposes only.
This is an example of the system aaa-server radius server command:

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius
	dnRouter(cfg-system-aaa-radius)# server priority 1 address 192.168.1.1
	dnRouter(cfg-aaa-radius-server)# vrf default
	dnRouter(cfg-aaa-radius-server)# password enc-!@#$%
	dnRouter(cfg-aaa-radius-server)# authenticaion enabled
	dnRouter(cfg-aaa-radius-server)# port 100
	dnRouter(cfg-aaa-radius-server)# retries 3
	dnRouter(cfg-aaa-radius-server)# retry-interval 20
	dnRouter(cfg-system-aaa-radius)# server priority 2 address 192.168.1.2
	dnRouter(cfg-aaa-radius-server)# vrf mgmt0
	dnRouter(cfg-aaa-radius-server)# password enc-!@#$%
	dnRouter(cfg-aaa-radius-server)# authenticaion enabled
	dnRouter(cfg-aaa-radius-server)# port 100
	dnRouter(cfg-aaa-radius-server)# retries 5
	dnRouter(cfg-aaa-radius-server)# retry-interval 15
	dnRouter(cfg-system-aaa-radius)# server priority 5 address 1134:1134::1
	dnRouter(cfg-aaa-radius-server)# vrf mgmt0
	dnRouter(cfg-aaa-radius-server)# password enc-!@#$%
	dnRouter(cfg-aaa-radius-server)# authenticaion enabled
	dnRouter(cfg-aaa-radius-server)# port 100
	dnRouter(cfg-aaa-radius-server)# retries 5
	dnRouter(cfg-aaa-radius-server)# retry-interval 15
