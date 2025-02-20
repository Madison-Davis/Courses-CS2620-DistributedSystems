import unittest
from unittest.mock import MagicMock
import grpc
import sys
import os

# Ensure that the parent directory is on the path so that the client module can be imported.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.chat_client import ChatClient
from comm import chat_pb2

class TestChatClient(unittest.TestCase):
    def setUp(self):
        # Use a dummy server address (won't actually connect because we will mock the stub)
        self.client = ChatClient(server_address="dummy:1234")
        # Replace the gRPC stub with a MagicMock to simulate server responses.
        self.client.stub = MagicMock()

    def test_create_account_success(self):
        # Simulate a successful account creation.
        success_response = chat_pb2.GenericResponse(success=True, message="Account created")
        self.client.stub.CreateAccount.return_value = success_response
        result = self.client.create_account("user1", "hash")
        self.assertTrue(result)

        # Simulate account creation failure (e.g., username already exists).
        failure_response = chat_pb2.GenericResponse(success=False, message="Username already exists")
        self.client.stub.CreateAccount.return_value = failure_response
        result = self.client.create_account("user1", "hash")
        self.assertFalse(result)

    def test_login_success(self):
        # Prepare a LoginResponse with one old message, one inbox message, and one draft.
        login_response = chat_pb2.LoginResponse(
            success=True,
            message="Login successful",
            inbox_count=2,
            old_messages=[
                chat_pb2.Message(msg_id=1, username="user1", sender="user2", msg="Hello", checked=False, inbox=False)
            ],
            inbox_messages=[
                chat_pb2.Message(msg_id=2, username="user1", sender="user3", msg="Hi", checked=False, inbox=True)
            ],
            drafts=[
                chat_pb2.Draft(draft_id=1, username="user1", recipient="user4", msg="Draft message", checked=False)
            ]
        )
        self.client.stub.Login.return_value = login_response
        inbox_count, old_messages, inbox_messages, drafts = self.client.login("user1", "hash")
        self.assertEqual(inbox_count, 2)
        self.assertEqual(len(old_messages), 1)
        self.assertEqual(len(inbox_messages), 1)
        self.assertEqual(len(drafts), 1)

    def test_send_message_success(self):
        send_response = chat_pb2.SendMessageResponse(success=True, message="Message sent", msg_id=100)
        self.client.stub.SendMessage.return_value = send_response
        msg_id = self.client.send_message(draft_id=1, recipient="recipient", sender="sender", content="Hello")
        self.assertEqual(msg_id, 100)

    def test_download_message_success(self):
        response = chat_pb2.GenericResponse(success=True, message="Downloaded")
        self.client.stub.DownloadMessage.return_value = response
        result = self.client.download_message("user1", 1)
        self.assertTrue(result)

    def test_check_message_success(self):
        response = chat_pb2.GenericResponse(success=True, message="Checked")
        self.client.stub.CheckMessage.return_value = response
        result = self.client.check_message("user1", 1)
        self.assertTrue(result)

    def test_delete_message_success(self):
        response = chat_pb2.GenericResponse(success=True, message="Deleted")
        self.client.stub.DeleteMessage.return_value = response
        result = self.client.delete_message("user1", 1)
        self.assertTrue(result)

    def test_add_draft_success(self):
        response = chat_pb2.AddDraftResponse(success=True, message="Draft added", draft_id=10)
        self.client.stub.AddDraft.return_value = response
        draft_id = self.client.add_draft("user1", "recipient", "message", False)
        self.assertEqual(draft_id, 10)

    def test_save_drafts_success(self):
        response = chat_pb2.GenericResponse(success=True, message="Draft saved")
        self.client.stub.SaveDrafts.return_value = response
        # Passing an empty list for drafts; you can extend this test with a list of Draft objects.
        result = self.client.save_drafts("user1", [])
        self.assertTrue(result)

    def test_logout_success(self):
        response = chat_pb2.GenericResponse(success=True, message="Logged out")
        self.client.stub.Logout.return_value = response
        result = self.client.logout("user1")
        self.assertTrue(result)

    def test_list_accounts_success(self):
        response = chat_pb2.ListAccountsResponse(success=True, message="Accounts fetched", usernames=["user1", "user2"])
        self.client.stub.ListAccounts.return_value = response
        usernames = self.client.list_accounts()
        self.assertEqual(usernames, ["user1", "user2"])

    def test_delete_account_success(self):
        response = chat_pb2.GenericResponse(success=True, message="Deleted")
        self.client.stub.DeleteAccount.return_value = response
        result = self.client.delete_account("user1")
        self.assertTrue(result)

    def test_get_password_success(self):
        response = chat_pb2.GetPasswordResponse(success=True, message="Password found", password_hash="hashed")
        self.client.stub.GetPassword.return_value = response
        pwd_hash = self.client.get_password("user1")
        self.assertEqual(pwd_hash, "hashed")

    def test_receive_messages(self):
        # Create a fake stream that yields two messages.
        fake_responses = [
            chat_pb2.ReceiveMessageResponse(
                msg_id=1, username="user1", sender="user2", msg="Hello", inbox_count=1
            ),
            chat_pb2.ReceiveMessageResponse(
                msg_id=2, username="user1", sender="user3", msg="Hi", inbox_count=2
            )
        ]
        # Set the ReceiveMessageStream to return an iterator over fake responses.
        self.client.stub.ReceiveMessageStream.return_value = iter(fake_responses)
        callback = MagicMock()
        self.client.receive_messages("user1", callback)
        # Verify that the callback was called for each message.
        self.assertEqual(callback.call_count, 2)
        first_call_args = callback.call_args_list[0][0][0]
        self.assertEqual(first_call_args.msg_id, 1)
        self.assertEqual(first_call_args.username, "user1")
        self.assertEqual(first_call_args.sender, "user2")
        self.assertEqual(first_call_args.msg, "Hello")

    def test_receive_messages_immediate_error(self):
        # Simulate the streaming call raising an RpcError immediately.
        self.client.stub.ReceiveMessageStream.side_effect = grpc.RpcError("Stream closed unexpectedly")
        callback = MagicMock()
        # The method catches the RpcError, so callback should never be called.
        self.client.receive_messages("user1", callback)
        self.assertEqual(callback.call_count, 0)

if __name__ == '__main__':
    unittest.main()
