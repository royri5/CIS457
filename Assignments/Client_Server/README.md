**Author:**
        
Richard Roy + some provided code

**Desc:**
        
Separate client and server programs that interact and transport data between each other.
In order to meet assignment specifications, the client sends a password to the server that
meets some arbitrary specifications.

**Running Instructions:**

First, start server.py, the clients will be unable to start without an available server.
Then, start as many clients as desired, each client must submit a password that matches
the assignment's specifications before it terminates. It may attempt infinitely many times.

**Password Specifications:**

The password must be a 6 digit number (with each individual digit summing to an even number)
followed by a space and a "word" that posesses an even number of chars.
Additionally, the 6 digit number must be greater than the seed, which is randomly generated
by each server.

**Notes:**

There is no clean end to the server as it is configured to remain open for as many clients 
as needed. KeyboardInterrupt does give a warning, but this did not matter for the assignment
so I am leaving it.
