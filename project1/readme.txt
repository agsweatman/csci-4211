Jon Huhn
huhnx025
CSCI 4211
Project 1

## Compilation ##
I implemented the project in Python 3, specifically version 3.6.3. I also tested
it on the CSELabs machines which use version 3.5.2. Run the server with
'python3 DNSServerV3.py' and the client with 'python3 DNSClientV3.py'.

## Implementation Description ##
First, the server creates a new TCP socket, binds it to port 5001 which the clients will connect to, and begins to listen for connections from the clients. The server then spawns a new thread to listen for when the user tells it to exit. Lastly, the server enters its main loop where it accepts connections from clients until the user exits the server.

When it receives a DNS query, the first thing it does is spawn a new thread to handle the request. This way, the server can keep accepting connections and handling other requests concurrently. Then, it check whether or not the query forms a valid URL. My implementation checks against a regular expression that looks for alphanumeric characters or hyphens separated by periods. This probably isn't a perfect regex, but it should catch most URLs. Anything that doesn't match returns "Invalid Format" to the client.

If the client's request matches the regex, then the server opens the cache file, creating it if it does not exist. Then, it looks for the client's request in the cache file line by line. If the host is found in the cache, then its IP is returned to the client, choosing a random IP if multiple are in the cache. If the request is not found in the cache, then the root DNS is queried and the response is cached. It caches here because it just made the root DNS request and can use that for other requests.

The server needs one socket to accept connections from clients and another to communicate back to clients. The first is bound to a specific name so the clients can find it. The other is a different port so that the server can communicate with multiple clients concurrently.
