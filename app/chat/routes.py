"""Web chat API routes."""
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict
import uuid
from app.chat.handler import get_chat_handler

logger = structlog.get_logger(__name__)
router = APIRouter()


# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    active_connections[session_id] = websocket

    logger.info("websocket_connected", session_id=session_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": "Connected to SureFlights! Type 'hi' to start."
        })

        handler = get_chat_handler()

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")

            logger.info("websocket_message_received", session_id=session_id, message=message[:100])

            # Process message
            response = await handler.handle_message(session_id, message)

            # Send response
            await websocket.send_json({
                "type": "bot",
                "message": response.get("message"),
                "payment_link": response.get("payment_link")
            })

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", session_id=session_id)
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        if session_id in active_connections:
            del active_connections[session_id]


@router.get("/chat", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the chat interface page."""
    # Generate a unique session ID
    session_id = str(uuid.uuid4())

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SureFlights - Book Your Flight</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}

        .chat-container {{
            width: 100%;
            max-width: 500px;
            height: 600px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .chat-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}

        .chat-header h1 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}

        .chat-header p {{
            font-size: 14px;
            opacity: 0.9;
        }}

        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }}

        .message {{
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }}

        .message.user {{
            justify-content: flex-end;
        }}

        .message-bubble {{
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}

        .message.bot .message-bubble {{
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .message.user .message-bubble {{
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }}

        .message.system .message-bubble {{
            background: #ffc107;
            color: #333;
            max-width: 100%;
            text-align: center;
        }}

        .chat-input-container {{
            padding: 15px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }}

        .chat-input {{
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
        }}

        .chat-input:focus {{
            border-color: #667eea;
        }}

        .send-button {{
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px 24px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background 0.3s;
        }}

        .send-button:hover {{
            background: #5568d3;
        }}

        .send-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}

        .connection-status {{
            padding: 8px;
            text-align: center;
            font-size: 12px;
            background: #ffc107;
            color: #333;
        }}

        .connection-status.connected {{
            background: #4caf50;
            color: white;
        }}

        .payment-link {{
            display: inline-block;
            background: #4caf50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            margin-top: 10px;
            font-weight: 600;
        }}

        .payment-link:hover {{
            background: #45a049;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .message {{
            animation: fadeIn 0.3s ease-out;
        }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>✈️ SureFlights</h1>
            <p>Book Nigerian domestic flights instantly</p>
        </div>

        <div id="connectionStatus" class="connection-status">Connecting...</div>

        <div id="chatMessages" class="chat-messages">
            <!-- Messages will appear here -->
        </div>

        <div class="chat-input-container">
            <input
                type="text"
                id="messageInput"
                class="chat-input"
                placeholder="Type your message..."
                disabled
            />
            <button id="sendButton" class="send-button" disabled>Send</button>
        </div>
    </div>

    <script>
        const sessionId = '{session_id}';
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${{wsProtocol}}//${{window.location.host}}/ws/chat/${{sessionId}}`;

        let socket;
        const messagesContainer = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const connectionStatus = document.getElementById('connectionStatus');

        function connectWebSocket() {{
            socket = new WebSocket(wsUrl);

            socket.onopen = () => {{
                console.log('WebSocket connected');
                connectionStatus.textContent = 'Connected ✓';
                connectionStatus.className = 'connection-status connected';
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.focus();
            }};

            socket.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                addMessage(data.message, data.type || 'bot', data.payment_link);
            }};

            socket.onerror = (error) => {{
                console.error('WebSocket error:', error);
                connectionStatus.textContent = 'Connection error';
                connectionStatus.className = 'connection-status';
            }};

            socket.onclose = () => {{
                console.log('WebSocket disconnected');
                connectionStatus.textContent = 'Disconnected';
                connectionStatus.className = 'connection-status';
                messageInput.disabled = true;
                sendButton.disabled = true;
            }};
        }}

        function addMessage(text, type = 'bot', paymentLink = null) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{type}}`;

            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';

            // Convert markdown-style bold to HTML
            let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formattedText = formattedText.replace(/\*(.*?)\*/g, '<em>$1</em>');

            bubbleDiv.innerHTML = formattedText;

            // Add payment link if provided
            if (paymentLink) {{
                const linkElement = document.createElement('a');
                linkElement.href = paymentLink;
                linkElement.className = 'payment-link';
                linkElement.textContent = 'Complete Payment →';
                linkElement.target = '_blank';
                bubbleDiv.appendChild(document.createElement('br'));
                bubbleDiv.appendChild(linkElement);
            }}

            messageDiv.appendChild(bubbleDiv);
            messagesContainer.appendChild(messageDiv);

            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }}

        function sendMessage() {{
            const message = messageInput.value.trim();
            if (!message || !socket || socket.readyState !== WebSocket.OPEN) {{
                return;
            }}

            // Add user message to UI
            addMessage(message, 'user');

            // Send to server
            socket.send(JSON.stringify({{ message: message }}));

            // Clear input
            messageInput.value = '';
        }}

        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});

        // Connect on page load
        connectWebSocket();
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)
