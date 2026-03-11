Error Messages
--------------

The proper syntax of an error messages is defined in this `Confluence <https://drivenets.atlassian.net/wiki/spaces/VP/pages/367919217/DNOS+CLI+Terminal+messaging>`__ page.

All the messages MUST follow a unified syntax & keyword. An error message typically has 3 parts:

Declaration, failed action, and reason for failure.

-  The "declaration" is followed by a colon

-  The "failed action" is followed by a comma

-  The "reason for failure" is followed by a full stop

**Example**

Error: Unable to configure interface <interface-name>, <interface-name> does not exist.

Warning: Configuringsystem timing-mode manual, may result in system synchronization error with the conductor.

The following cases are identified as **errors**:

- The command syntax is invalid / not-supported

- The parameter syntax is invalid / not-supported

- Faliure to commit the candidate configuration (due to syntax or resource issues)

The following cases are identified as **warnings**:

- Performing an operational command which may result in an intrusive action (such as "request system restart").

- Applying a candidate configuration commit which may result in a non-stable state.

**Capitalization**

Error messages follow the regular capitalization rules:

 - Use a capital letter after a full stop or a colon

- Use capital letters for acronyms

- Use a lowercase letter after a comma

- The "declaration" always begins with a capital letter: **E**  rror:

- The "reason for failure" begins with a lowercase letter (as it follows a comma).

**Example**

Error: Unable to configure interface <interface-name>, <interface-name> does not exist.

Expected output:

Error: Unable to configure interface <interface-name>, ge100-1/2/1 does not exist.

Error: Unable to remove VRF <vrf-name>, interfaces are attached to the VRF.

**Phrasing**

$type: $cause to $action[exact command] ,[reason for faliure]

The "failed action" has the general phrasing: "$cause to $action," ("Unable to do something,"). Always use the adjective Unable. Do not use "Cannot do something" or "Failed to do something". See `Exceptions <#_Exceptions>`__ below.

Avoid using contractions in error messages.

**Example**

Error: Unable to configure interface ge100-1/2/1.100 qos policy out myQoSPolicy1, policy does not exist.

Warning: Configuring system timing-mode manual, may result in system synchronization error with the conductor.

**Exceptions**

The reason for failure may at times be unnecessary.

Error: Bad mask /24 for address 192.168.1.0.

Error: Unauthorized to execute the command.

Error: No TACACS servers are available. Please reconnect to CLI.

Error: Unknown command.

Error: Command not supported by current system.

When entering a wrong value for a paramater, the failed action phrasing should be: Error: Invalid value for [parameter-name], value must be x-y.

**Example**

Error:Invalid value for probe-interval, value must be 1..300.
