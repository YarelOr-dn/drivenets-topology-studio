System AAA Overview
-------------------

TACACS+ and RADIUS are security protocols that provide a central validation of users attempting to gain access to a router or network access server. The protocols enable remote Authentication, Authorization, and Accounting (AAA) services to be handled separately on different servers (DNOS supports RADIUS only for authentication).

Authentication - when a user attempts to log in to DNOS (TACACS+/RADIUS client), the authentication request is sent to the TACACS+/RADIUS server. The server determines if the user is allowed access to the system.
Authentication servers must all be of the same type,
Authorization - if the user is granted access by the TACACS+/RADIUS authentication server, the authorization request is sent to the TACACS+ server. The server determines the level of access to grant the user based on the configuration.
Accounting - the user's actions and the connection time is logged for billing and auditing. TACACS+ tracks login requests, configuration changes and entered commands.

The supported AAA combinations are:
+--------+----------------+---------------+------------+
| Option | Authentication | Authorization | Accounting |
+--------+----------------+---------------+------------+
| 1      | RADIUS         | TACACS        | TACACS     |
+--------+----------------+---------------+------------+
| 2      | TACACS         | TACACS        | TACACS     |
+--------+----------------+---------------+------------+

You can configure multiple TACACS+ servers for each function or multiple RADIUS servers for authentication. On each TACACS+ server you can enable each function separately, e.g. you can have separate TACACS+ servers for authorization and separate for accounting.

If you have multiple authentication servers configured, and the first server on the list is unreachable or the router doesn't receive its replies, the user authentication will be done against the other servers on the list until the router receives a response from one of them. Similarly, if you have multiple authorization or accounting servers configured, the user authorization or accounting will be performed against the servers on the list until a response is received from one of them.

If some of the servers for a specific function are down (such as all Authentication servers), there will be a fallback to local.