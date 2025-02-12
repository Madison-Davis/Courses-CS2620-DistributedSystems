# tests_custom.py



# +++++++++++++ Imports and Installs +++++++++++++ #

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import server_custom



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
        
        request = "testuser:hashedpassword"
        response = server_custom.process_request(0x0003, request, mock_conn)
        self.assertEqual(response, "ok")
    
    @patch('server.sqlite3.connect')
    def test_server_login_success(self, mock_sqlite):
        """Test successful login with correct credentials."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        
        request = "testuser:hashedpassword"
        response = server_custom.process_request(0x0001, request, mock_conn)
        self.assertEqual(response, "[0,[],[],[]]")
    
    @patch('server.sqlite3.connect')
    def test_server_login_failure(self, mock_sqlite):
        """Test login failure due to incorrect credentials."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        request = "username:wrongpassword"
        response = server_custom.process_request(0x0001, request, mock_conn)
        self.assertEqual(response, "error:invalid")
    
    @patch('server.sqlite3.connect')
    def test_server_list_accounts(self, mock_sqlite):
        """Test listing all user accounts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("user1",), ("user2",), ("testuser",)]
        
        request = ""
        response = server_custom.process_request(0x0004, request, mock_conn)
        self.assertIn("testuser", response)
    
    @patch('server.sqlite3.connect')
    def test_server_send_message(self, mock_sqlite):
        """Test sending a message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # User exists
        
        request = "1:testuser:senderuser:Hello!"
        
        response = server_custom.process_request(0x0002, request, mock_conn)
        self.assertEqual(response, "1")
    
    @patch('server.sqlite3.connect')
    def test_server_delete_message(self, mock_sqlite):
        """Test deleting a message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        request = "testuser:1"
        response = server_custom.process_request(0x000A, request, mock_conn)
        self.assertEqual(response, "ok")
    
    @patch('server.sqlite3.connect')
    def test_server_delete_account(self, mock_sqlite):
        """Test deleting an account."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        request = "username:hashedpassword"
        response = server_custom.process_request(0x000B, request, mock_conn)
        self.assertEqual(response, "ok")
    
if __name__ == '__main__':
    unittest.main()