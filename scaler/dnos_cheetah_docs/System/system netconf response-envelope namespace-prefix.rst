system netconf response-envelope namespace-prefix
-------------------------------------------------

**Minimum user role:** operator

Configure the NETCONF response to use prefix namespaces or not. By default the response includes prefix namespaces.

**Command syntax: namespace-prefix [prefix-enabled]**

**Command mode:** config

**Hierarchies**

- system netconf response-envelope

**Note**

- When the namespace prefix is enabled this is the NETCONF response:
  <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data xmlns:ietf-netconf-monitoring="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
  <ietf-netconf-monitoring:netconf-state>
- When the namespace prefix is disabled this is the NETCONF response:
  <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
  <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">


**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------------+---------+
| Parameter      | Description                                                                      | Range             | Default |
+================+==================================================================================+===================+=========+
| prefix-enabled | determinate if NETCONF response will use prefix namespaces or not, by default    | enabled, disabled | enabled |
|                | the response will include prefix namespaces.                                     |                   |         |
+----------------+----------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)# response-envelope
    dnRouter(cfg-netconf-response-envelope)# namespace-prefix enabled


**Removing Configuration**

To revert the namespace-prefix to default:
::

    dnRouter(cfg-netconf-response-envelope)# no namespace-prefix

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
