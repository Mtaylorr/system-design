# Backend Engineering Notes

## Glossary

- [Communication Design Patterns](#communication-design-patterns)
  - [Patterns](#patterns)
    - [Request-Response](#request-response)
      - [Anatomy](#anatomy)
    - [Synchronous vs Asynchronous](#synchronous-vs-asynchronous)
    - [Push](#push)
    - [Short Polling](#short-polling)
    - [Long Polling](#long-polling)
    - [Server-Sent Events](#server-sent-events)
    - [Stateful vs Stateless](#stateful-vs-stateless)
    - [Sidecar](#sidecar)
- [Protocols](#protocols)
  - [Protocol Properties](#protocol-properties)
  - [OSI Model](#osi-model)
  - [Internet Protocol](#internet-protocol)
  - [UDP](#udp)
  - [TCP](#tcp)
  - [TLS](#tls)
  - [HTTP/1.1](#http11)
  - [HTTPS, TLS, Keys and Certificates](#https-tls-keys-and-certificates)
  - [WebSockets](#websockets)
  - [HTTP/2](#http2)
  - [HTTP/3](#http3)
  - [gRPC](#grpc)
  - [WebRTC](#webrtc)
- [Resources](#resources)

## Communication Design Patterns

### Patterns

#### Request-Response

- A client sends a request to a server and waits for a response.
- Common in HTTP APIs, RPC calls, database queries, and service-to-service calls.
- Best for direct interactions where the caller needs an immediate result or confirmation.
- The server processes the request synchronously from the client's point of view.

##### Anatomy

- Client: the caller that starts the interaction.
- Request: the message sent by the client, usually containing an operation, headers, and optional body data.
- Server: the receiver that handles the request.
- Processing: the server validates, runs logic, reads or writes data, then prepares a result.
- Response: the message returned to the client, usually containing a status code, headers, and optional body data.

##### Strengths

- Simple mental model.
- Easy to debug and trace.
- Works well for read operations and quick commands.
- Natural fit for REST, GraphQL queries, and many RPC-style APIs.

##### Tradeoffs

- The caller is blocked while waiting for the response.
- Latency matters because the user or service is usually waiting.
- Tightens coupling between caller and responder availability.
- Can struggle with long-running work unless paired with async processing, queues, polling, or callbacks.

##### Example

- Browser requests `GET /users/123`; the backend returns the user profile.

##### Python Client Example

- File: `request_response_client.py`

- The client sends a request with `requests.get(...)`.
- The client waits until the server sends a response or the request times out.
- The response includes a status code and, usually, response data.

#### Synchronous vs Asynchronous

- Synchronous communication means the caller waits for the operation to finish before continuing.
- Asynchronous communication means the caller starts the operation and continues without waiting for the final result immediately.

##### Synchronous

- Best when the caller needs an immediate answer.
- Common with HTTP request-response APIs, RPC calls, and database queries.
- Example: a checkout service asks the payment service to authorize a card and waits for the result.

How it works internally:

- The caller sends the request and keeps execution tied to that operation.
- A thread, coroutine, or event-loop task waits for the response.
- If the implementation is blocking, the thread cannot do other useful work while waiting for network or disk I/O.
- If the implementation is non-blocking, the runtime can pause that operation and resume it when the response is ready.
- The caller usually receives either a success response, an error response, or a timeout.

##### Asynchronous

- Best for long-running work, background processing, retries, and decoupling services.
- Common with queues, events, streams, background jobs, and message brokers.
- Example: an order service publishes an `OrderCreated` event, and the email service sends the confirmation later.

How it works internally:

- The producer creates a message, event, or job.
- The message is stored in a queue, broker, log, or task table.
- The producer continues after the message is accepted, without waiting for the final work to finish.
- A consumer picks up the message later and processes it independently.
- The result may be stored, emitted as another event, sent by callback, or observed through polling.
- Failed work can usually be retried without forcing the original caller to stay connected.

##### Context Switching

- Context switching means the system pauses one unit of work and resumes another.
- In blocking synchronous code, waiting threads can cause expensive operating system context switches because the scheduler moves CPU time between threads.
- Too many blocked threads can increase memory use and reduce throughput.
- In asynchronous code, context switching often happens at the application runtime level, such as an event loop switching between tasks when I/O is pending.
- Async context switches are usually lighter than OS thread switches, but they still add complexity because execution resumes later, often in a different part of the code.
- The main performance win of async is not that work becomes faster; it is that the system can use waiting time to handle other work.

##### Tradeoffs

- Synchronous systems are easier to reason about but depend on the availability and latency of the other service.
- Asynchronous systems are more resilient and scalable but require handling eventual consistency, retries, ordering, and observability.

#### Push

- Push communication means the server sends data to the client when new information is available.
- The client does not need to repeatedly ask for updates.
- Common in real-time notifications, chat, live dashboards, multiplayer games, monitoring systems, and collaborative apps.

##### How It Works Internally

- The client first establishes a connection or subscription.
- The server keeps track of which clients are interested in which updates.
- When new data is available, the server sends the update directly to subscribed clients.
- The client receives the update and reacts immediately.
- The connection may stay open for a long time, depending on the protocol.

##### Common Technologies

- WebSockets: full-duplex connection where client and server can both send messages.
- Server-Sent Events: server pushes text-based events over a long-lived HTTP connection.
- Push notifications: platform-managed delivery for mobile, web, or desktop notifications.
- Message brokers: services can push messages to consumers subscribed to a queue or topic.

##### Strengths

- Low latency for updates.
- Avoids wasteful polling.
- Good fit for real-time user experiences.
- Can reduce unnecessary client requests.

##### Tradeoffs

- Requires connection management.
- Harder to scale than simple request-response.
- Clients may disconnect, reconnect, or miss messages.
- The server needs to handle backpressure when clients cannot keep up.
- Usually needs heartbeats, retries, and reconnection logic.

##### Example

- A chat server pushes a new message to all users currently connected to the room.

#### Short Polling

- Short polling means the client repeatedly asks the server for updates at a fixed interval.
- Each poll is a normal request-response interaction.
- Common when real-time updates are useful but a persistent connection is not needed or not available.

##### How It Works Internally

- The client sends a request like `GET /notifications`.
- The server immediately returns the current state or available updates.
- The client waits for a short delay.
- The client sends the same request again.
- This cycle continues while the page, app, or process is active.

##### Strengths

- Simple to build and debug.
- Works with regular HTTP infrastructure.
- Does not require long-lived connections.
- Easy to add to existing request-response APIs.

##### Tradeoffs

- Can waste requests when there are no updates.
- Higher latency than push because updates are only seen on the next poll.
- Polling too often increases server load.
- Polling too slowly makes the user experience feel stale.

##### Example

- A frontend checks `GET /job-status/123` every five seconds until a background job is complete.

#### Long Polling

- Long polling means the client asks the server for updates, but the server holds the request open until new data is available or a timeout is reached.
- After the client receives a response, it immediately sends another request.
- It gives a near-real-time experience while still using regular HTTP request-response.

##### How It Works Internally

- The client sends a request like `GET /messages`.
- If the server has new data, it responds immediately.
- If there is no new data, the server keeps the request open.
- When new data arrives, the server responds to the waiting request.
- If no data arrives before the timeout, the server returns an empty response.
- The client then opens a new long-polling request.

##### Strengths

- Lower latency than short polling.
- Reduces unnecessary empty responses.
- Works over normal HTTP.
- Useful when WebSockets or server-sent events are not available.

##### Tradeoffs

- The server must manage many open requests.
- Timeouts and reconnect behavior must be handled carefully.
- Still has more overhead than a true persistent streaming connection.
- Load balancers and proxies need compatible timeout settings.

##### Example

- A messaging app keeps a `GET /room/123/messages` request open until a new message arrives.

#### Server-Sent Events

- Server-Sent Events, or SSE, let the server continuously send events to the client over a single long-lived HTTP connection.
- Communication is one-way: server to client.
- Common in live feeds, notifications, dashboards, logs, progress updates, and status streams.

##### How It Works Internally

- The client opens an HTTP connection using the browser `EventSource` API.
- The server responds with a stream using the `text/event-stream` content type.
- The server keeps the connection open.
- Whenever new data is available, the server writes an event to the stream.
- The client receives each event without creating a new request.
- If the connection drops, the browser can reconnect automatically.

##### Strengths

- Simpler than WebSockets for server-to-client updates.
- Works over regular HTTP.
- Built-in browser reconnection support.
- Good fit when the client only needs to receive updates.

##### Tradeoffs

- One-way only; the client still uses normal HTTP requests to send data back.
- Long-lived connections must be managed by the server.
- Not ideal for binary data or high-frequency bidirectional messaging.
- Proxy and load balancer buffering can interfere if not configured correctly.

##### Example

- A deployment dashboard streams build logs and progress updates from the server to the browser.

#### Stateful vs Stateless

- Stateless communication means each request contains everything the server needs to handle it.
- Stateful communication means the server remembers information about the client or session across multiple interactions.

##### Stateless

- The server does not rely on stored session context from previous requests.
- Each request includes identity, permissions, parameters, and required data.
- Common in REST APIs using tokens such as JWTs or API keys.
- Easier to scale because any server instance can handle any request.

##### Stateful

- The server stores context about the client, connection, or workflow.
- Later requests can depend on information saved from earlier interactions.
- Common in login sessions, shopping carts, WebSocket connections, multiplayer games, and database connections.
- Can be useful when repeated interactions need shared context.

##### Tradeoffs

- Stateless systems are simpler to scale, cache, retry, and load balance.
- Stateless requests can become larger because repeated context must be sent each time.
- Stateful systems can reduce repeated data transfer and support richer interactions.
- Stateful systems are harder to scale because session data must be stored, shared, replicated, or pinned to a server.

##### Example

- Stateless: each API request sends an authorization token.
- Stateful: a chat server keeps a WebSocket connection and room membership for each connected client.

#### Sidecar

- The sidecar pattern runs a helper process or container next to the main application instance.
- The sidecar is not the business service itself; it provides supporting infrastructure behavior for that service.
- Common sidecar responsibilities include proxying traffic, service discovery, retries, mTLS, metrics, logging, tracing, config reloads, secret rotation, and protocol translation.
- In Kubernetes, this usually means the application container and sidecar container run inside the same pod.

##### How It Works Internally

- The application and sidecar are deployed together as one runtime unit.
- They usually share the same lifecycle: when the app instance starts, the sidecar starts; when the app instance is removed, the sidecar is removed too.
- They can communicate through `localhost`, Unix domain sockets, shared volumes, or environment-specific networking.
- The sidecar can handle infrastructure concerns without requiring every application team to implement those concerns in their service code.
- From the platform point of view, every application replica may get its own sidecar replica.

##### Traffic Models

- Explicit local call: the application intentionally calls the sidecar, often through `localhost`.
- Inbound proxying: traffic reaches the sidecar first, then the sidecar forwards it to the app.
- Outbound proxying: the app sends traffic out, but the sidecar intercepts or receives it before it leaves the pod.
- Shared-volume agent: the sidecar writes files, certificates, config, or logs to a shared volume that the application reads.

In a service mesh, the sidecar often acts as a local data-plane proxy:

- The app sends a request to another service.
- Traffic is routed through the sidecar proxy.
- The sidecar applies policies such as mTLS, retries, timeouts, circuit breaking, load balancing, and telemetry.
- The receiving service's sidecar accepts the traffic, validates it, and forwards it to the receiving app.

##### Why Senior Engineers Use It

- It separates platform concerns from product code.
- It creates a consistent operational layer across many services.
- It allows infrastructure behavior to evolve without rewriting every application.
- It keeps service teams focused on domain logic while the platform team manages cross-cutting behavior.
- It is especially useful when many services need the same non-functional behavior, such as security, observability, or traffic policy.

##### Operational Details

- Resource cost is multiplied by the number of replicas: `100` app replicas means `100` sidecars.
- The sidecar shares the app's failure domain, so sidecar issues can break an otherwise healthy app instance.
- Startup ordering matters if the app depends on the sidecar being ready.
- Shutdown and draining matter because the sidecar may still be forwarding in-flight requests.
- Readiness checks should account for both the app and sidecar when traffic depends on both.
- Logs, metrics, and traces should make it clear whether latency or failures came from the app or the sidecar.

##### Strengths

- Reduces duplicated infrastructure code across services.
- Enables consistent security and observability.
- Can add capabilities without changing application binaries.
- Works well for per-instance behavior, such as local proxying, local log shipping, or local certificate handling.

##### Tradeoffs

- Adds latency because traffic may pass through another process.
- Adds memory and CPU overhead to every service replica.
- Makes debugging harder because failures may happen in the app, sidecar, network rules, or control-plane configuration.
- Can hide behavior from application developers if traffic is intercepted transparently.
- Requires strong operational discipline around configuration, versioning, rollout, and rollback.

##### When To Use It

- Use it when the concern is cross-cutting, infrastructure-heavy, and needed consistently across many services.
- Use it when behavior needs to be close to each app instance, such as local proxying, local credentials, or per-instance telemetry.
- Use it when platform teams need a standard way to enforce networking, security, or observability policies.

##### When To Avoid It

- Avoid it for simple business logic that belongs in the application.
- Avoid it when a centralized service or library would solve the problem with less operational overhead.
- Avoid it if the added latency, resource cost, or failure surface is larger than the value of the abstraction.

##### Example

- A payment API runs with an Envoy sidecar. The application sends normal HTTP requests, while the sidecar handles mTLS, retries, request metrics, and routing policy for calls to other internal services.

## Protocols

### Protocol Properties

- A protocol defines how systems communicate: message format, ordering rules, connection behavior, error handling, timing, and expected semantics.
- Senior engineers evaluate protocols by their operational properties, not only by their feature list.

#### Core Properties

- Connection-oriented vs connectionless: whether communication has a maintained session, such as TCP, or independent messages, such as UDP.
- Reliable vs best-effort: whether the protocol guarantees delivery, retransmission, and recovery from loss.
- Ordered vs unordered: whether messages must arrive in the same order they were sent.
- Stream vs message-oriented: whether data is treated as a continuous byte stream or as discrete messages.
- Stateful vs stateless: whether protocol participants remember previous interactions.
- Full-duplex vs half-duplex: whether both sides can send at the same time.
- Flow control: protecting the receiver from being overwhelmed.
- Congestion control: protecting the network from being overwhelmed.
- Framing: how the receiver knows where one message starts and ends.
- Multiplexing: carrying many logical conversations over one connection.
- Security: authentication, confidentiality, integrity, replay protection, and downgrade resistance.

#### Senior Design Concerns

- Protocol choice affects latency, failure modes, observability, load balancing, and scaling.
- The same application behavior can feel very different over TCP, UDP, HTTP/1.1, HTTP/2, HTTP/3, WebSockets, or gRPC.
- Always ask what the system needs more: reliability, low latency, ordering, bidirectional messaging, browser compatibility, simple operations, or efficient streaming.
- Protocols also shape operational tooling: logs, packet captures, traces, metrics, retries, timeouts, and proxy behavior differ by protocol.

### OSI Model

- The OSI model is a conceptual seven-layer model for thinking about network communication.
- Real systems do not always map perfectly to OSI, but it is useful for debugging and design conversations.

#### Layers

- Layer 1, Physical: electrical, radio, fiber, cables, signals.
- Layer 2, Data Link: local network frames, MAC addresses, Ethernet, Wi-Fi.
- Layer 3, Network: IP addressing and routing between networks.
- Layer 4, Transport: process-to-process transport, such as TCP and UDP.
- Layer 5, Session: session management; often blended into application protocols today.
- Layer 6, Presentation: encoding, serialization, compression, encryption; often blended into TLS or application code.
- Layer 7, Application: HTTP, gRPC, DNS, SMTP, WebSockets, and business-facing protocols.

#### Senior Design Concerns

- Debug from lower layers upward: link, IP routing, transport connection, TLS, then application protocol.
- A failure that looks like an application bug may actually be DNS, MTU, packet loss, TLS validation, proxy buffering, or load balancer behavior.
- The model helps isolate ownership: network team, platform team, application team, security team, or vendor.
- In modern backend systems, layers are often crossed by proxies, service meshes, NAT, CDNs, and API gateways.

### Internet Protocol

- Internet Protocol, or IP, is the network-layer protocol responsible for addressing and routing packets between hosts.
- IP is best-effort: it does not guarantee delivery, ordering, uniqueness, or latency.
- TCP, UDP, QUIC, ICMP, and many other protocols run on top of IP.

#### How It Works Internally

- Each packet has a source IP, destination IP, and metadata such as TTL or hop limit.
- Routers forward packets hop by hop toward the destination.
- Packets can be dropped, delayed, reordered, or fragmented depending on network conditions.
- IPv4 uses 32-bit addresses; IPv6 uses 128-bit addresses and removes many IPv4-era constraints.
- NAT rewrites addresses and ports so private networks can share public addresses.

#### Senior Design Concerns

- MTU matters: packets larger than the path can handle may be fragmented or dropped.
- Fragmentation is risky for performance and reliability; protocols often avoid it through path MTU discovery.
- Private IPs, public IPs, NAT, firewalls, and security groups affect reachability.
- Anycast can route users to the nearest healthy edge, but routing shifts can change latency and traffic patterns.
- ICMP is important for diagnostics and path MTU discovery; blocking all ICMP can create subtle outages.
- IP does not know about users, requests, services, or transactions; higher layers must provide those semantics.

#### Failure Modes

- Routing blackholes, asymmetric routing, packet loss, MTU issues, NAT exhaustion, firewall drops, and DNS pointing to unreachable addresses.

### UDP

- UDP is a transport protocol that sends independent datagrams without creating a connection.
- It provides ports and checksums, but it does not provide delivery guarantees, ordering, retransmission, or congestion control.
- Common uses include DNS, VoIP, video, gaming, telemetry, and QUIC.

#### How It Works Internally

- The sender places data in a UDP datagram and sends it to an IP address and port.
- The receiver either receives the entire datagram or does not receive it.
- UDP preserves message boundaries: one send maps to one datagram at the transport layer.
- If reliability, retries, ordering, or congestion control are needed, the application or a higher-level protocol must implement them.

#### Senior Design Concerns

- UDP is useful when latency matters more than perfect delivery.
- Keep payloads below practical MTU limits to avoid fragmentation.
- NAT and firewall behavior can be harder with UDP than TCP.
- UDP services can be abused for reflection and amplification attacks if responses are larger than requests.
- Applications need explicit handling for loss, duplication, reordering, jitter, and rate control.
- QUIC shows that UDP can support reliable streams, but that reliability is implemented above UDP.

#### When To Use It

- Use it for latency-sensitive traffic, simple request-response protocols like DNS, or protocols that implement their own transport behavior.

#### When To Avoid It

- Avoid raw UDP when the application needs reliable ordered delivery and you do not want to build that machinery yourself.

### TCP

- TCP is a connection-oriented transport protocol that provides a reliable, ordered byte stream between two endpoints.
- It is the foundation for HTTP/1.1, HTTP/2, traditional TLS, many databases, SSH, SMTP, and many internal service protocols.

#### How It Works Internally

- TCP starts with a three-way handshake: SYN, SYN-ACK, ACK.
- Data is split into segments with sequence numbers.
- The receiver acknowledges received data.
- Lost data is retransmitted.
- Flow control prevents the sender from overwhelming the receiver.
- Congestion control adjusts sending rate based on network conditions.
- TCP presents data as a byte stream, so applications need framing to separate messages.

#### Senior Design Concerns

- TCP reliability creates head-of-line blocking: missing earlier bytes block later bytes in the same stream.
- Connection setup costs matter; use connection pooling and keep-alive for frequent calls.
- Tail latency can be affected by packet loss, retransmission timeouts, congestion windows, and slow start.
- Long-lived TCP connections need health checks, keepalives, idle timeout awareness, and graceful draining.
- Too many short-lived connections can exhaust ephemeral ports or overload load balancers.
- Nagle's algorithm, delayed ACKs, socket buffers, and congestion control can affect latency-sensitive systems.

#### Failure Modes

- Half-open connections, connection resets, idle timeout drops, SYN floods, retransmission storms, ephemeral port exhaustion, and slow consumers.

### TLS

- TLS provides authentication, confidentiality, and integrity for communication over an untrusted network.
- It is commonly used with HTTP as HTTPS, but it can secure many application protocols.
- Modern TLS uses asymmetric cryptography for authentication and key exchange, then symmetric encryption for efficient data transfer.

#### How It Works Internally

- The client starts a TLS handshake and sends supported versions, cipher suites, SNI, and ALPN.
- The server presents a certificate proving its identity.
- The client validates the certificate chain against trusted certificate authorities.
- Both sides derive shared session keys.
- Application data is encrypted and authenticated using those session keys.
- Session resumption can reduce handshake cost for repeat connections.

#### Senior Design Concerns

- TLS protects data in transit, not data at rest or data after termination.
- Certificate lifecycle is operationally critical: issuance, rotation, expiration, revocation, and monitoring.
- TLS termination location matters: edge proxy, load balancer, service mesh, application, or end-to-end.
- mTLS authenticates both client and server and is common in zero-trust service-to-service networks.
- ALPN lets clients and servers negotiate protocols such as HTTP/1.1 or HTTP/2.
- TLS adds latency during handshake, but persistent connections and resumption reduce the impact.
- Weak ciphers, old protocol versions, and bad certificate validation can make TLS look present but not meaningful.

#### Failure Modes

- Expired certificates, wrong hostnames, broken trust chains, clock skew, unsupported cipher suites, TLS version mismatch, and misconfigured SNI.

### HTTP/1.1

- HTTP/1.1 is an application protocol for request-response communication.
- It uses methods, URLs, headers, status codes, and optional bodies.
- It usually runs over TCP, with TLS added when using HTTPS.

#### How It Works Internally

- A client sends a textual request line, headers, and optionally a body.
- The server returns a status line, headers, and optionally a body.
- Persistent connections allow multiple requests over the same TCP connection.
- Chunked transfer encoding allows streaming a response when the final size is not known upfront.
- Pipelining exists but is rarely used in browsers because of head-of-line blocking and compatibility issues.

#### Senior Design Concerns

- HTTP method semantics matter: `GET` should be safe, `PUT` and `DELETE` should be idempotent, and `POST` often is not.
- Status codes are part of the API contract and should distinguish client errors, server errors, retries, and conflicts.
- Headers carry critical metadata: auth, content type, caching, tracing, idempotency, and feature negotiation.
- Connection pools, keep-alive settings, and idle timeouts strongly affect performance.
- HTTP/1.1 has per-connection head-of-line blocking, so clients often open multiple connections.
- Proxies, caches, and gateways can change behavior through buffering, compression, rewriting, and timeouts.

#### Failure Modes

- Connection exhaustion, slowloris-style slow clients, oversized headers, bad timeout alignment, proxy buffering, ambiguous retries, and accidental non-idempotent writes.

### HTTPS, TLS, Keys and Certificates

- HTTPS is HTTP carried over TLS.
- TLS secures the transport; certificates and keys establish identity and enable encrypted sessions.
- A certificate binds a public key to a hostname or identity, and a private key proves control of that identity.

#### How It Works Internally

- The server owns a private key and presents a certificate containing the matching public key.
- The certificate is signed by a certificate authority, often through an intermediate CA.
- The client validates the chain from the server certificate up to a trusted root CA.
- The hostname must match the certificate's Subject Alternative Name.
- After validation and key exchange, HTTP traffic flows inside the encrypted TLS session.

#### Senior Design Concerns

- Private keys must be protected; compromise means attackers can impersonate the service.
- Automate certificate issuance and renewal with systems such as ACME where possible.
- Monitor expiration aggressively because certificate outages are common and highly visible.
- Use HSTS carefully to force browsers to use HTTPS, but understand rollback implications.
- Decide where TLS terminates and whether traffic is re-encrypted to the backend.
- mTLS can provide strong service identity but adds certificate distribution and rotation complexity.
- Certificate pinning is rarely worth the operational risk unless the threat model is very specific.

#### Failure Modes

- Expired certs, missing intermediate certificates, wrong SAN, leaked private keys, mixed-content browser issues, TLS termination gaps, and inconsistent certificates across regions.

### WebSockets

- WebSockets provide a long-lived, full-duplex communication channel between client and server.
- They are commonly used for chat, collaborative editing, live dashboards, multiplayer games, notifications, and interactive systems.

#### How It Works Internally

- The client starts with an HTTP request that asks to upgrade the connection.
- If the server accepts, the connection switches from HTTP request-response to WebSocket frames.
- Both sides can send messages independently at any time.
- Messages can be text or binary.
- Ping and pong frames are used for liveness checks.

#### Senior Design Concerns

- WebSockets are a transport, not a complete messaging system; delivery guarantees, replay, ordering beyond the connection, and auth refresh are application concerns.
- Horizontal scaling requires connection routing, presence tracking, and usually pub/sub between server instances.
- Backpressure matters because slow clients can accumulate queued messages.
- Load balancers must support long-lived upgraded connections and graceful draining.
- Authentication should be checked at connection time and often revalidated for sensitive subscriptions.
- Reconnect logic should include jitter, resume tokens, and state refresh.

#### Failure Modes

- Silent disconnects, stale subscriptions, memory growth from slow clients, deploys dropping connections, sticky-session imbalance, and missed messages during reconnect.

### HTTP/2

- HTTP/2 is a binary, multiplexed version of HTTP that usually runs over TLS in browsers.
- It keeps HTTP semantics while changing how requests and responses are framed on the wire.

#### How It Works Internally

- One TCP connection can carry many concurrent streams.
- Each stream contains frames for headers, data, and control messages.
- HPACK compresses headers to reduce repeated metadata overhead.
- Flow control exists at both connection and stream levels.
- ALPN is commonly used during TLS negotiation to select HTTP/2.

#### Senior Design Concerns

- Multiplexing reduces the need for many TCP connections.
- Packet loss still causes TCP-level head-of-line blocking across all streams on the connection.
- Server push existed in HTTP/2 but is rarely useful in modern browser deployments.
- Stream concurrency limits must be tuned for clients, servers, and proxies.
- gRPC commonly uses HTTP/2 because it supports efficient multiplexing and streaming.
- Debugging is harder than HTTP/1.1 because frames are binary and behavior depends on intermediaries.

#### Failure Modes

- Misconfigured stream limits, proxy incompatibility, connection-level flow control stalls, TCP packet loss affecting all streams, and uneven load across long-lived connections.

### HTTP/3

- HTTP/3 keeps HTTP semantics but runs over QUIC instead of TCP.
- QUIC runs over UDP and includes TLS 1.3 security, multiplexing, congestion control, and connection management.

#### How It Works Internally

- The client and server establish a QUIC connection over UDP.
- TLS 1.3 is integrated into the QUIC handshake.
- Multiple independent streams can share the same connection.
- Packet loss on one stream does not block delivery on other streams at the transport layer.
- QUIC connection IDs allow connection migration, such as moving from Wi-Fi to mobile networks.

#### Senior Design Concerns

- HTTP/3 reduces transport-level head-of-line blocking compared with HTTP/2 over TCP.
- UDP must be allowed through networks, firewalls, and load balancers.
- Fallback to HTTP/2 or HTTP/1.1 is still important because not every path handles QUIC well.
- QUIC can improve mobile and lossy-network performance, but CPU cost and operational visibility may differ from TCP.
- Observability and packet capture are different because QUIC encrypts more transport metadata.
- Edge/CDN support often determines whether HTTP/3 is practical for public traffic.

#### Failure Modes

- UDP blocking, bad fallback behavior, load balancer incompatibility, excessive CPU at high throughput, and harder low-level debugging.

### gRPC

- gRPC is an RPC framework commonly built on HTTP/2 with Protocol Buffers.
- It is designed for strongly typed service-to-service communication.
- It supports unary calls, client streaming, server streaming, and bidirectional streaming.

#### How It Works Internally

- Services and messages are defined in `.proto` files.
- Code generation creates typed clients and servers.
- Calls are sent as HTTP/2 streams.
- Metadata carries headers, auth, tracing, and call configuration.
- Deadlines, status codes, and streaming are part of the framework model.

#### Senior Design Concerns

- gRPC is excellent for internal APIs where strong contracts and generated clients are valuable.
- Deadlines should be mandatory so calls do not hang indefinitely.
- Schema evolution matters: field numbers, optionality, backward compatibility, and deprecation need discipline.
- Retries must respect idempotency and deadline budgets.
- Browser clients usually need gRPC-Web or a gateway because native browser gRPC support is limited.
- Observability should expose method names, status codes, deadlines, payload sizes, and retry behavior.
- Load balancing can be tricky because gRPC connections are long-lived and multiplexed.

#### Failure Modes

- Missing deadlines, incompatible proto changes, oversized messages, connection imbalance, poor gateway translation, and hidden retry amplification.

### WebRTC

- WebRTC enables real-time peer-to-peer audio, video, and data communication.
- It is used for video calls, live collaboration, low-latency data channels, remote control, and interactive media.
- WebRTC is not one protocol; it combines several protocols and mechanisms.

#### How It Works Internally

- Signaling exchanges session metadata between peers, usually through an application-specific server.
- ICE discovers possible network paths between peers.
- STUN helps discover public-facing addresses behind NAT.
- TURN relays traffic when direct peer-to-peer connectivity fails.
- DTLS secures the connection.
- SRTP carries encrypted audio and video.
- SCTP over DTLS can provide data channels.

#### Senior Design Concerns

- Signaling is not standardized by WebRTC; your application must design and operate it.
- NAT traversal is the hard part, and TURN relay capacity can become expensive.
- Media systems often use SFUs to route streams efficiently for group calls.
- Low latency requires handling jitter, packet loss, adaptive bitrate, codec negotiation, and device changes.
- WebRTC is operationally more complex than WebSockets or HTTP because it mixes networking, media, encryption, and browser behavior.
- Security is strong by default for media transport, but identity, room authorization, and abuse prevention are still application responsibilities.

#### Failure Modes

- ICE failure, TURN overload, asymmetric NAT issues, codec mismatch, poor network adaptation, high packet loss, and signaling disconnects.

## Resources

- [Backend engineering playlist](https://www.youtube.com/watch?v=fhdPyoO6aXI&list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)
- [Fundamentals of Backend Communications and Protocols](https://www.udemy.com/course/fundamentals-of-backend-communications-and-protocols/learn/lecture/34629150?start=0#overview)
- [Database Engines Crash Course](https://www.udemy.com/course/database-engines-crash-course/learn/lecture/22515194?start=0)
- [Fundamentals of Networking for Effective Backend Design](https://www.udemy.com/course/fundamentals-of-networking-for-effective-backend-design/learn/lecture/31161082?start=0#overview)
