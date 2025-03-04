import unittest
import os
import socket
import threading
import time
import tempfile
import multiprocessing
import config
from vm import VirtualMachine

class TestVirtualMachine(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory for log files so tests do not interfere with production logs
        self.temp_log_dir = tempfile.TemporaryDirectory()
        self.original_log_dir = config.LOG_DIR
        config.LOG_DIR = self.temp_log_dir.name + "/"
        
        # Create a VirtualMachine instance with id = 0 for testing.
        self.vm = VirtualMachine(0)

    def tearDown(self):
        # Restore the original log directory and clean up temporary files
        config.LOG_DIR = self.original_log_dir
        self.temp_log_dir.cleanup()

    def test_initialization(self):
        # Check that the VM sets its id, port, and peer_ports correctly.
        self.assertEqual(self.vm.id, 0)
        self.assertEqual(self.vm.port, config.PORT + 0)
        for peer_id, peer_port in self.vm.peer_ports:
            self.assertNotEqual(peer_id, 0)
        # Check that the queue and queue_size are created.
        self.assertIsInstance(self.vm.queue, multiprocessing.queues.Queue)
        self.assertEqual(self.vm.logical_clock, 0)
        # Check that the log file exists and is empty.
        with open(self.vm.log_file, 'r') as f:
            self.assertEqual(f.read(), "")

    def test_update_without_sender(self):
        # Calling update without sender_logical_clock should increment the logical clock by 1.
        current_clock = self.vm.logical_clock
        self.vm.update()
        self.assertEqual(self.vm.logical_clock, current_clock + 1)

    def test_update_with_sender(self):
        # If a message is received, update should set the logical clock to max(current, sender) + 1.
        self.vm.logical_clock = 5
        self.vm.update(sender_logical_clock=7)
        self.assertEqual(self.vm.logical_clock, 8)
        
        # If local clock is already higher than sender, then it still increments by 1.
        self.vm.logical_clock = 10
        self.vm.update(sender_logical_clock=5)
        self.assertEqual(self.vm.logical_clock, 11)

    def test_log(self):
        # Ensure that a log message is correctly appended to the log file.
        test_message = "Test log entry"
        self.vm.log(test_message)
        with open(self.vm.log_file, 'r') as f:
            content = f.read()
        self.assertIn(test_message, content)

    def test_handle_queue(self):
        # Simulate a message arriving in the VM's queue.
        # We add a tuple: (sender_id, sender_logical_clock)
        initial_queue_length = self.vm.queue_size.value
        self.vm.queue.put((1, 10))
        with self.vm.queue_size.get_lock():
            self.vm.queue_size.value += 1
        
        self.vm.logical_clock = 5
        self.vm.handle_queue()
        # Expected logical clock update: max(5,10) + 1 = 11.
        self.assertEqual(self.vm.logical_clock, 11)
        # The queue_size should return to its previous value.
        self.assertEqual(self.vm.queue_size.value, initial_queue_length)
        # Also, the log file should contain an entry about receiving a message.
        with open(self.vm.log_file, 'r') as f:
            content = f.read()
        self.assertIn("Receive From 1", content)

    def test_send_msg_success(self):
        # Set up a dummy server socket that will accept a connection.
        dummy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_server_socket.bind(("localhost", 0))  # Bind to an ephemeral port.
        dummy_port = dummy_server_socket.getsockname()[1]
        dummy_server_socket.listen(1)

        def dummy_server():
            conn, _ = dummy_server_socket.accept()
            conn.close()
            dummy_server_socket.close()

        server_thread = threading.Thread(target=dummy_server)
        server_thread.start()
        # When a server is listening, send_msg should return True.
        result = self.vm.send_msg(dummy_port, "dummy message")
        self.assertTrue(result)
        server_thread.join()

    def test_send_msg_failure(self):
        # Try to send to a port where no server is running; expect failure.
        closed_port = 9999  # Assuming this port is not open.
        result = self.vm.send_msg(closed_port, "dummy message")
        self.assertFalse(result)

    def test_send_msg_and_update(self):
        # Override send_msg to always return True (bypassing real socket behavior)
        original_send_msg = self.vm.send_msg
        self.vm.send_msg = lambda recipient_port, msg: True

        initial_clock = self.vm.logical_clock
        # Use the peer_ports list from initialization (for id=0 with NUM_VIRTUAL_MACHINES=3, there are 2 recipients).
        recipients = self.vm.peer_ports
        self.vm.send_msg_and_update(recipients)
        # The logical clock should have been incremented once for each message sent.
        self.assertEqual(self.vm.logical_clock, initial_clock + len(recipients))

        # Check that the log file contains a send entry for each recipient.
        with open(self.vm.log_file, 'r') as f:
            content = f.read()
        for recipient in recipients:
            self.assertIn(f"Sent Msg To {recipient[0]}", content)

        # Restore the original send_msg method.
        self.vm.send_msg = original_send_msg

if __name__ == '__main__':
    unittest.main()
