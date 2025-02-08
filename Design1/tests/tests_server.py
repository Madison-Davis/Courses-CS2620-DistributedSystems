import unittest
import sqlite3
import json
import os
import sys

module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../server'))
sys.path.append(module_path)

from server import db_init, process_request

class TestChatDatabase(unittest.TestCase):
    
    def setUp(self):
        """Initialize a fresh in-memory database for each test."""
        self.db = sqlite3.connect(':memory:')
        self.cursor = self.db.cursor()
        db_init(self.db)  # Initialize tables
    
    def tearDown(self):
        """Close database connection after each test."""
        self.db.close()
    
    def test_create_account(self):
        """Test creating an account."""
        request = json.dumps({
            "actions": {
                "createAccount": {
                    "request": {"data": {"username": "testuser", "passwordHash": "12345"}},
                    "successResponse": {"status": "success"},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
    
    def test_login(self):
        """Test logging into an existing account."""
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", ("testuser", "12345", 0))
        self.db.commit()
        request = json.dumps({
            "actions": {
                "login": {
                    "request": {"data": {"username": "testuser", "passwordHash": "12345"}},
                    "successResponse": {"status": "success", "data": {}},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
    
    def test_list_accounts(self):
        """Test listing all accounts."""
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", ("testuser", "12345", 0))
        self.db.commit()
        request = json.dumps({
            "actions": {
                "listAccounts": {
                    "successResponse": {"status": "success", "data": {}},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
        self.assertIn("testuser", response["data"]["accounts_users"])
    
    def test_send_message(self):
        """Test sending a message to another user."""
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", ("sender", "pass", 1))
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", ("recipient", "pass", 1))
        self.db.commit()
        request = json.dumps({
            "actions": {
                "sendMessage": {
                    "request": {"data": {"user": "recipient", "sender": "sender", "content": "Hello!"}},
                    "successResponse": {"status": "success"},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
    
    def test_delete_message(self):
        """Test deleting a message."""
        self.cursor.execute("INSERT INTO messages (user, sender, msg, checked, inbox) VALUES (?, ?, ?, ?, ?)", ("recipient", "sender", "Hello!", 0, 1))
        self.db.commit()
        request = json.dumps({
            "actions": {
                "deleteMessage": {
                    "request": {"data": {"username": "sender", "msgId": 1}},
                    "successResponse": {"status": "success"},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
    
    def test_delete_account(self):
        """Test deleting an account."""
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", ("testuser", "12345", 1))
        self.db.commit()
        request = json.dumps({
            "actions": {
                "deleteAccount": {
                    "request": {"data": {"username": "testuser", "passwordHash": "12345"}},
                    "successResponse": {"status": "success"},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
    
    def test_logout(self):
        """Test logging out of an account."""
        self.cursor.execute("INSERT INTO accounts (user, pwd, logged_in) VALUES (?, ?, ?)", ("testuser", "12345", 1))
        self.db.commit()
        request = json.dumps({
            "actions": {
                "logout": {
                    "request": {"data": {"username": "testuser"}},
                    "successResponse": {"status": "success"},
                    "errorResponse": {"status": "error"}
                }
            }
        })
        response = json.loads(process_request(request, self.db))
        self.assertEqual(response["status"], "success")
    
if __name__ == '__main__':
    unittest.main()
