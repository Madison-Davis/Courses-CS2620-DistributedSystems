# tests_json.py



# +++++++++++++ Imports and Installs +++++++++++++ #

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import server



# +++++++++++++++++ Main Tests +++++++++++++++++ #

class TestChatApplication(unittest.TestCase):
    
    @patch('server.sqlite3.connect')
    def test_server_create_account(self, mock_sqlite):
        """Test creating a new account."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No existing user
        
        request = json.dumps({
            "actions": {
                "createAccount": {
                    "request": {"data": {"username": "testuser", "passwordHash": "hashedpassword"}}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "ok")
    
    @patch('server.sqlite3.connect')
    def test_server_login_success(self, mock_sqlite):
        """Test successful login with correct credentials."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        
        request = json.dumps({
            "actions": {
                "login": {
                    "request": {"data": {"username": "testuser", "passwordHash": "hashedpassword"}}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "ok")
    
    @patch('server.sqlite3.connect')
    def test_server_login_failure(self, mock_sqlite):
        """Test login failure due to incorrect credentials."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        request = json.dumps({
            "actions": {
                "login": {
                    "request": {"data": {"username": "testuser", "passwordHash": "wrongpassword"}}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "error")
    
    @patch('server.sqlite3.connect')
    def test_server_list_accounts(self, mock_sqlite):
        """Test listing all user accounts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("user1",), ("user2",), ("testuser",)]
        
        request = json.dumps({
            "actions": {
                "listAccounts": {
                    "request": {"data": {}}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "ok")
        self.assertIn("testuser", response_json["data"]["accounts_users"])
    
    @patch('server.sqlite3.connect')
    def test_server_send_message(self, mock_sqlite):
        """Test sending a message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # User exists
        
        request = json.dumps({
            "actions": {
                "sendMessage": {
                    "request": {"data": {
                        "draft_id": 1,
                        "recipient": "testuser",
                        "sender": "senderuser",
                        "content": "Hello!"
                    }}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "ok")
    
    @patch('server.sqlite3.connect')
    def test_server_delete_message(self, mock_sqlite):
        """Test deleting a message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        request = json.dumps({
            "actions": {
                "deleteMessage": {
                    "request": {"data": {"username": "testuser", "msgId": 1}}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "ok")
    
    @patch('server.sqlite3.connect')
    def test_server_delete_account(self, mock_sqlite):
        """Test deleting an account."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        request = json.dumps({
            "actions": {
                "deleteAccount": {
                    "request": {"data": {"username": "testuser", "passwordHash": "hashedpassword"}}
                }
            }
        })
        response = server.process_request(request, mock_conn)
        response_json = json.loads(response.decode("utf-8"))
        self.assertEqual(response_json["status"], "ok")
    
if __name__ == '__main__':
    unittest.main()