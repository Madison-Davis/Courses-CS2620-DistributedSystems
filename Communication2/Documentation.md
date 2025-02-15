# CS 2620 Communication 2: gRPC


-------------------------------------------
## Setup

Generate Python gRPC files from .proto definition:
`py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto`

Run server:
`py -m server.server`

Run client GUI:
`py -m client.gui`