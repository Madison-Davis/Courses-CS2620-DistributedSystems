# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: chat.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'chat.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nchat.proto\x12\x04\x63hat\"5\n\x12ReplicationRequest\x12\x0e\n\x06method\x18\x01 \x01(\t\x12\x0f\n\x07payload\x18\x02 \x01(\x0c\"\x12\n\x10HeartbeatRequest\"\"\n\x11HeartbeatResponse\x12\r\n\x05\x61live\x18\x01 \x01(\x08\"\x12\n\x10GetLeaderRequest\"<\n\x11GetLeaderResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x16\n\x0eleader_address\x18\x02 \x01(\t\"?\n\x14\x43reateAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x15\n\rpassword_hash\x18\x02 \x01(\t\"7\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x15\n\rpassword_hash\x18\x02 \x01(\t\"\xaf\x01\n\rLoginResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x13\n\x0binbox_count\x18\x03 \x01(\x05\x12#\n\x0cold_messages\x18\x04 \x03(\x0b\x32\r.chat.Message\x12%\n\x0einbox_messages\x18\x05 \x03(\x0b\x32\r.chat.Message\x12\x1b\n\x06\x64rafts\x18\x06 \x03(\x0b\x32\x0b.chat.Draft\"&\n\x12GetPasswordRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"N\n\x13GetPasswordResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x15\n\rpassword_hash\x18\x03 \x01(\t\"\x15\n\x13ListAccountsRequest\"K\n\x14ListAccountsResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x11\n\tusernames\x18\x03 \x03(\t\"Z\n\x12SendMessageRequest\x12\x10\n\x08\x64raft_id\x18\x01 \x01(\x05\x12\x11\n\trecipient\x18\x02 \x01(\t\x12\x0e\n\x06sender\x18\x03 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x04 \x01(\t\"G\n\x13SendMessageResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0e\n\x06msg_id\x18\x03 \x01(\x05\"X\n\x0f\x41\x64\x64\x44raftRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\trecipient\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\x12\x0f\n\x07\x63hecked\x18\x04 \x01(\x08\"F\n\x10\x41\x64\x64\x44raftResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x10\n\x08\x64raft_id\x18\x03 \x01(\x05\"B\n\x11SaveDraftsRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x1b\n\x06\x64rafts\x18\x02 \x03(\x0b\x32\x0b.chat.Draft\"7\n\x13\x43heckMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x0e\n\x06msg_id\x18\x02 \x01(\x05\":\n\x16\x44ownloadMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x0e\n\x06msg_id\x18\x02 \x01(\x05\"8\n\x14\x44\x65leteMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x0e\n\x06msg_id\x18\x02 \x01(\x05\"(\n\x14\x44\x65leteAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"!\n\rLogoutRequest\x12\x10\n\x08username\x18\x01 \x01(\t\")\n\x15ReceiveMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"l\n\x16ReceiveMessageResponse\x12\x0e\n\x06msg_id\x18\x01 \x01(\x05\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x0e\n\x06sender\x18\x03 \x01(\t\x12\x0b\n\x03msg\x18\x04 \x01(\t\x12\x13\n\x0binbox_count\x18\x05 \x01(\x05\"h\n\x07Message\x12\x0e\n\x06msg_id\x18\x01 \x01(\x05\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x0e\n\x06sender\x18\x03 \x01(\t\x12\x0b\n\x03msg\x18\x04 \x01(\t\x12\x0f\n\x07\x63hecked\x18\x05 \x01(\x08\x12\r\n\x05inbox\x18\x06 \x01(\x08\"\\\n\x05\x44raft\x12\x10\n\x08\x64raft_id\x18\x01 \x01(\x05\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x11\n\trecipient\x18\x03 \x01(\t\x12\x0b\n\x03msg\x18\x04 \x01(\t\x12\x0f\n\x07\x63hecked\x18\x05 \x01(\x08\"3\n\x0fGenericResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"E\n\x15UpdateRegistryRequest\x12\x0b\n\x03pid\x18\x01 \x01(\x05\x12\x11\n\ttimestamp\x18\x02 \x01(\x02\x12\x0c\n\x04\x61\x64\x64r\x18\x03 \x01(\t2\xb5\t\n\x0b\x43hatService\x12\x42\n\rCreateAccount\x12\x1a.chat.CreateAccountRequest\x1a\x15.chat.GenericResponse\x12\x30\n\x05Login\x12\x12.chat.LoginRequest\x1a\x13.chat.LoginResponse\x12\x42\n\x0bGetPassword\x12\x18.chat.GetPasswordRequest\x1a\x19.chat.GetPasswordResponse\x12\x45\n\x0cListAccounts\x12\x19.chat.ListAccountsRequest\x1a\x1a.chat.ListAccountsResponse\x12\x42\n\x0bSendMessage\x12\x18.chat.SendMessageRequest\x1a\x19.chat.SendMessageResponse\x12\x39\n\x08\x41\x64\x64\x44raft\x12\x15.chat.AddDraftRequest\x1a\x16.chat.AddDraftResponse\x12<\n\nSaveDrafts\x12\x17.chat.SaveDraftsRequest\x1a\x15.chat.GenericResponse\x12@\n\x0c\x43heckMessage\x12\x19.chat.CheckMessageRequest\x1a\x15.chat.GenericResponse\x12\x46\n\x0f\x44ownloadMessage\x12\x1c.chat.DownloadMessageRequest\x1a\x15.chat.GenericResponse\x12\x42\n\rDeleteMessage\x12\x1a.chat.DeleteMessageRequest\x1a\x15.chat.GenericResponse\x12\x42\n\rDeleteAccount\x12\x1a.chat.DeleteAccountRequest\x1a\x15.chat.GenericResponse\x12\x34\n\x06Logout\x12\x13.chat.LogoutRequest\x1a\x15.chat.GenericResponse\x12S\n\x14ReceiveMessageStream\x12\x1b.chat.ReceiveMessageRequest\x1a\x1c.chat.ReceiveMessageResponse0\x01\x12<\n\tReplicate\x12\x18.chat.ReplicationRequest\x1a\x15.chat.GenericResponse\x12<\n\tHeartbeat\x12\x16.chat.HeartbeatRequest\x1a\x17.chat.HeartbeatResponse\x12<\n\tGetLeader\x12\x16.chat.GetLeaderRequest\x1a\x17.chat.GetLeaderResponse\x12\x44\n\x0eUpdateRegistry\x12\x1b.chat.UpdateRegistryRequest\x1a\x15.chat.GenericResponse\x12K\n\x15UpdateRegistryReplica\x12\x1b.chat.UpdateRegistryRequest\x1a\x15.chat.GenericResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_REPLICATIONREQUEST']._serialized_start=20
  _globals['_REPLICATIONREQUEST']._serialized_end=73
  _globals['_HEARTBEATREQUEST']._serialized_start=75
  _globals['_HEARTBEATREQUEST']._serialized_end=93
  _globals['_HEARTBEATRESPONSE']._serialized_start=95
  _globals['_HEARTBEATRESPONSE']._serialized_end=129
  _globals['_GETLEADERREQUEST']._serialized_start=131
  _globals['_GETLEADERREQUEST']._serialized_end=149
  _globals['_GETLEADERRESPONSE']._serialized_start=151
  _globals['_GETLEADERRESPONSE']._serialized_end=211
  _globals['_CREATEACCOUNTREQUEST']._serialized_start=213
  _globals['_CREATEACCOUNTREQUEST']._serialized_end=276
  _globals['_LOGINREQUEST']._serialized_start=278
  _globals['_LOGINREQUEST']._serialized_end=333
  _globals['_LOGINRESPONSE']._serialized_start=336
  _globals['_LOGINRESPONSE']._serialized_end=511
  _globals['_GETPASSWORDREQUEST']._serialized_start=513
  _globals['_GETPASSWORDREQUEST']._serialized_end=551
  _globals['_GETPASSWORDRESPONSE']._serialized_start=553
  _globals['_GETPASSWORDRESPONSE']._serialized_end=631
  _globals['_LISTACCOUNTSREQUEST']._serialized_start=633
  _globals['_LISTACCOUNTSREQUEST']._serialized_end=654
  _globals['_LISTACCOUNTSRESPONSE']._serialized_start=656
  _globals['_LISTACCOUNTSRESPONSE']._serialized_end=731
  _globals['_SENDMESSAGEREQUEST']._serialized_start=733
  _globals['_SENDMESSAGEREQUEST']._serialized_end=823
  _globals['_SENDMESSAGERESPONSE']._serialized_start=825
  _globals['_SENDMESSAGERESPONSE']._serialized_end=896
  _globals['_ADDDRAFTREQUEST']._serialized_start=898
  _globals['_ADDDRAFTREQUEST']._serialized_end=986
  _globals['_ADDDRAFTRESPONSE']._serialized_start=988
  _globals['_ADDDRAFTRESPONSE']._serialized_end=1058
  _globals['_SAVEDRAFTSREQUEST']._serialized_start=1060
  _globals['_SAVEDRAFTSREQUEST']._serialized_end=1126
  _globals['_CHECKMESSAGEREQUEST']._serialized_start=1128
  _globals['_CHECKMESSAGEREQUEST']._serialized_end=1183
  _globals['_DOWNLOADMESSAGEREQUEST']._serialized_start=1185
  _globals['_DOWNLOADMESSAGEREQUEST']._serialized_end=1243
  _globals['_DELETEMESSAGEREQUEST']._serialized_start=1245
  _globals['_DELETEMESSAGEREQUEST']._serialized_end=1301
  _globals['_DELETEACCOUNTREQUEST']._serialized_start=1303
  _globals['_DELETEACCOUNTREQUEST']._serialized_end=1343
  _globals['_LOGOUTREQUEST']._serialized_start=1345
  _globals['_LOGOUTREQUEST']._serialized_end=1378
  _globals['_RECEIVEMESSAGEREQUEST']._serialized_start=1380
  _globals['_RECEIVEMESSAGEREQUEST']._serialized_end=1421
  _globals['_RECEIVEMESSAGERESPONSE']._serialized_start=1423
  _globals['_RECEIVEMESSAGERESPONSE']._serialized_end=1531
  _globals['_MESSAGE']._serialized_start=1533
  _globals['_MESSAGE']._serialized_end=1637
  _globals['_DRAFT']._serialized_start=1639
  _globals['_DRAFT']._serialized_end=1731
  _globals['_GENERICRESPONSE']._serialized_start=1733
  _globals['_GENERICRESPONSE']._serialized_end=1784
  _globals['_UPDATEREGISTRYREQUEST']._serialized_start=1786
  _globals['_UPDATEREGISTRYREQUEST']._serialized_end=1855
  _globals['_CHATSERVICE']._serialized_start=1858
  _globals['_CHATSERVICE']._serialized_end=3063
# @@protoc_insertion_point(module_scope)
