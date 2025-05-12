from typing import List, Optional, Union
from PyQt6.QtWidgets import QStatusBar, QMenu
from PyQt6.QtCore import QTimer, Qt


class EnhancedStatusBar(QStatusBar):
    """
    An enhanced status bar that can display timed messages, keep track of message history,
    and provide a right-click menu to view recent messages.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the enhanced status bar.
        
        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        
        # Initialize message history
        self._message_history: List[str] = []
        self._max_history_size: int = 10
        
        # Message timer
        self._message_timer: QTimer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self._clearTimedMessage)
        
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)
    
    def showMessage(self, message: str, timeout: Union[int, float] = 0) -> None:
        """
        Display a message in the status bar.
        
        Args:
            message: The message to display
            timeout: Time in milliseconds before the message disappears.
                     If 0, the message will remain until replaced.
        """
        # Add message to history
        self._addToHistory(message)
        
        # Display message
        super().showMessage(message)
        
        # Set up timer if needed
        if timeout > 0:
            self._message_timer.stop()  # Stop any existing timer
            self._message_timer.setInterval(int(timeout))
            self._message_timer.start()
    
    def showTemporaryMessage(self, message: str, timeout: Union[int, float] = 3000) -> None:
        """
        Display a temporary message that will disappear after the specified timeout.
        
        Args:
            message: The message to display
            timeout: Time in milliseconds before the message disappears (default: 3000)
        """
        self.showMessage(message, timeout)
    
    def showPermanentMessage(self, message: str) -> None:
        """
        Display a permanent message that will remain until replaced.
        
        Args:
            message: The message to display
        """
        self.showMessage(message, 0)
    
    def _addToHistory(self, message: str) -> None:
        """
        Add a message to the history, maintaining maximum size.
        
        Args:
            message: The message to add
        """
        # Add message to the beginning for most recent first
        self._message_history.insert(0, message)
        
        # Trim history if needed
        if len(self._message_history) > self._max_history_size:
            self._message_history = self._message_history[:self._max_history_size]
    
    def _clearTimedMessage(self) -> None:
        """Clear the current message when the timer expires."""
        super().clearMessage()
    
    def _showContextMenu(self, position) -> None:
        """
        Show context menu with message history when right-clicked.
        
        Args:
            position: The position where the menu should be shown
        """
        # Create context menu
        context_menu = QMenu(self)
        context_menu.setTitle("Recent Messages")
        
        # Add message history to menu
        if not self._message_history:
            # If no messages in history
            no_messages_action = context_menu.addAction("No recent messages")
            no_messages_action.setEnabled(False)
        else:
            # Add message history items
            for message in self._message_history:
                # Truncate long messages for the menu
                display_text = message[:60] + "..." if len(message) > 60 else message
                context_menu.addAction(display_text)
        
        # Show context menu at the right-click position
        context_menu.exec(self.mapToGlobal(position))
    
    def setMaxHistorySize(self, size: int) -> None:
        """
        Set the maximum number of messages to keep in history.
        
        Args:
            size: The maximum history size
        """
        if size < 1:
            raise ValueError("History size must be at least 1")
        
        self._max_history_size = size
        
        # Trim history if needed
        if len(self._message_history) > self._max_history_size:
            self._message_history = self._message_history[:self._max_history_size]
    
    def clearHistory(self) -> None:
        """Clear the message history."""
        self._message_history.clear() 