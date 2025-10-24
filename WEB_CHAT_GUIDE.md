# Web Chat Widget - User Guide

## ✅ COMPLETED!

Your web chat booking widget is now live and ready to test!

## 🌐 Access the Chat

### Local Testing:
```
http://localhost:8001/chat
```

### Via ngrok (Public Access):
```
https://unopiated-michel-magically.ngrok-free.dev/chat
```

You can share the ngrok link with anyone to test the booking flow!

## 🎯 Features

✅ **Real-time Chat** - WebSocket-powered instant messaging
✅ **Flight Search** - Search Nigerian domestic flights
✅ **AI-free Parsing** - No OpenAI needed (uses regex patterns)
✅ **Session Management** - Maintains conversation state
✅ **Payment Integration** - Generates Paystack payment links
✅ **Responsive Design** - Works on mobile and desktop
✅ **Professional UI** - Modern, clean interface

## 📱 How to Use (Test Flow)

### Step 1: Start Conversation
Open the chat and type:
```
Hi
```

Expected: Welcome message with instructions

### Step 2: Search for Flight
Type:
```
Flight from Lagos to Abuja on 2025-11-15
```

Expected: List of 1-5 flight options with prices

### Step 3: Select Flight
Type:
```
1
```

Expected: Request for passenger details

### Step 4: Enter Passenger Info
Type:
```
Name: John Doe
Email: john@example.com
Phone: +2348012345678
DOB: 1990-01-15
```

Expected: Booking summary

### Step 5: Confirm Booking
Type:
```
confirm
```

Expected: Booking confirmation with payment link!

### Step 6: Complete Payment
Click the green "Complete Payment →" button

Expected: Redirected to Paystack payment page

## 🛠️ Technical Details

### Architecture:
```
Frontend (HTML/JS)
    ↓ WebSocket
Backend (FastAPI)
    ↓
Chat Handler
    ↓
Flight Search → Duffel API
Booking → Payment → Paystack API
```

### Session Management:
- Each chat session gets a unique UUID
- Sessions stored in memory (clears on server restart)
- Full conversation state tracked

### File Structure:
```
app/chat/
├── __init__.py
├── session.py      # Session management
├── handler.py      # Message processing
└── routes.py       # WebSocket & HTTP routes
```

## 🎨 Customization

### Change Colors:
Edit `app/chat/routes.py`, look for gradient colors:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

Replace with your brand colors!

### Change Logo/Name:
In the chat header HTML:
```html
<h1>✈️ SureFlights</h1>
<p>Book Nigerian domestic flights instantly</p>
```

## 🔍 Supported Search Formats

The chat recognizes these patterns:

**Cities:**
- Lagos, LOS
- Abuja, ABV
- Port Harcourt, PHC, PH
- Kano, KAN
- Enugu, ENU

**Date Format:**
- YYYY-MM-DD (e.g., 2025-11-15)

**Example Searches:**
```
Flight from Lagos to Abuja on 2025-11-15
LOS to ABV on 2025-12-01
Lagos to Port Harcourt on 2025-11-20
```

## 🚀 Deployment Options

### Option 1: Keep Using ngrok (Testing)
- Current setup works perfectly
- Share ngrok URL with testers
- Free tier has limits on concurrent connections

### Option 2: Deploy to Render/Railway (Production)
- Permanent URL
- Always available
- Free tier available
- Example: https://sureflights.onrender.com/chat

### Option 3: Add to Your Website
- Embed as iframe or popup
- Custom domain
- Professional appearance

## 📊 Monitoring

Watch server logs for chat activity:

```bash
# Good signs:
[info] websocket_connected session_id=...
[info] chat_message_received text=...
[info] chat_search_success offers=5

# Issues:
[error] chat_search_error
[error] websocket_error
```

## 🐛 Troubleshooting

### Chat Won't Connect
- Check server is running: http://localhost:8001/health
- Check browser console for WebSocket errors
- Try refreshing the page

### Search Returns No Results
- Check date format is YYYY-MM-DD
- Verify Duffel API is working
- Check server logs for errors

### Booking Fails
- Check Paystack credentials in .env
- Verify passenger info format
- Check server logs

## 🎉 What's Next?

You now have a **fully functional web-based flight booking chat**!

### Immediate Next Steps:
1. Test the full booking flow
2. Try different search patterns
3. Complete a test booking
4. Check payment link works

### Future Enhancements:
- Add user authentication
- Save chat history to database
- Add file uploads for passport
- Multi-language support
- Mobile app integration
- Analytics dashboard

## 💡 Tips

**Best Practice:**
- Always use YYYY-MM-DD for dates
- Include all passenger details in one message
- Test with real flight dates

**Pro Tip:**
You can embed this chat widget on any website:
```html
<iframe
  src="https://your-domain.com/chat"
  width="400"
  height="600"
  frameborder="0"
></iframe>
```

## 📞 Support

If users get stuck, they can:
- Type `help` for assistance
- Type `cancel` to start over
- Refresh page for new session

---

**Congratulations! Your web chat booking system is live! 🎊**

Test it now at: http://localhost:8001/chat
