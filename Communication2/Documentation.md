# CS 2620 Communication 2: gRPC


-------------------------------------------
## Setup

Generate Python gRPC files: Navigate to comm/ and run `py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto`
Replace `import chat_pb2 as chat__pb2` with `from comm import chat_pb2 as chat__pb2` in `chat_pb2_grpc.py`

Run server:
`py -m server.server`

Run client GUI:
`py -m client.gui`


-------------------------------------------
## Code Structure

```
├── client
│   ├── chat_client.py
│   ├── gui.py
├── comm
│   ├── chat.proto
│   ├── chat_pb2.py
│   ├── chat_pb2_grpc.py
├── config
│   ├── config.py
├── server
│   ├── server.py
│   ├── server_security.py
└── Documentation.md
```

The user interface is run on `gui.py`, which instantiates a `ChatClient` and makes function calls to it. In `chat_client.py`, the `ChatClient` makes calls to a Chat Service Stub, which has its request and response types outlined in `chat.proto`. A `ChatService` is instantiated with the setup tasks of database initialization. When the `ChatService` receives an action request, it implements the appropriate SQL calls in `server.py`. 