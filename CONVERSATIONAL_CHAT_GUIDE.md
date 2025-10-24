# Conversational AI Chat - User Guide

## 🎉 NEW FEATURES!

Your web chat is now **conversational and intelligent!** It can discuss flight options with you like a real travel agent.

## 🤖 What's New

### 1. **Natural Language Understanding**
Chat naturally - no rigid formats needed!

**Examples:**
```
"I need to get to Abuja from Lagos next week"
"Find me the cheapest flight to Port Harcourt"
"Show me flights from Kano to Lagos on November 15th"
```

### 2. **Discuss Flight Results**
Ask questions about the search results!

**After seeing flight options, you can ask:**
- "Which is the cheapest?"
- "Which is fastest?"
- "What do you recommend?"
- "Which has the best value?"
- "Tell me about option 2"
- "Compare all the flights"

### 3. **Date Range Search**
Find the cheapest day to fly!

**Examples:**
```
"Find cheapest flights from Lagos to Abuja between Nov 10 and Nov 17"
"Search Lagos to Abuja from 2025-11-10 to 2025-11-17"
```

Bot will show you:
- Cheapest date highlighted
- Prices for each day
- Recommendation for best travel date

### 4. **Smart Recommendations**
The AI analyzes and recommends based on:
- **Cheapest**: Lowest price
- **Fastest**: Shortest flight time
- **Best Value**: Balance of price and time

## 💬 Example Conversations

### Simple Search & Discussion
```
You: Hi
Bot: Welcome! I'll help you book flights...

You: I need to fly from Lagos to Abuja on November 15th
Bot: 🔍 Searching for flights...
[Shows 5 flight options]

You: Which is cheapest?
Bot: 💰 The cheapest option is Option 2 - Air Peace for ₦45,000.
     This is the most affordable choice!
     Type the number (1-5) when you're ready to book!

You: What about fastest?
Bot: ⚡ The fastest option is Option 1 - Aero at 1h 10m.
     Gets you there quickest!

You: Which do you recommend?
Bot: ⭐ I'd recommend Option 3 - Dana Air for ₦52,000 (1h 15m).
     It's the best balance of price and travel time!

You: 3
Bot: ✅ Flight selected! Now I need passenger details...
```

### Date Range Search
```
You: Find me the cheapest flights from Lagos to Abuja from Nov 10 to Nov 17

Bot: 🔍 Searching flights from LOS to ABV between 2025-11-10 and 2025-11-17...

Bot: 📊 Price Comparison: LOS → ABV

     💰 Cheapest: 2025-11-13 at ₦42,500

     Prices by date:
     • 2025-11-10: from ₦58,000
     • 2025-11-11: from ₦55,000
     • 2025-11-12: from ₦48,000
     • 2025-11-13: from ₦42,500 ⭐
     • 2025-11-14: from ₦47,000
     • 2025-11-15: from ₦56,000
     • 2025-11-16: from ₦59,000
     • 2025-11-17: from ₦54,000

     Would you like to see flights for 2025-11-13? (yes/no)

You: yes
Bot: [Shows flight options for Nov 13]

You: Book option 1
Bot: [Continues with booking...]
```

### Natural Language
```
You: I have a meeting in Abuja next Tuesday, what are my options?
Bot: I'd love to help! What city are you flying from? And what's the exact date?

You: From Lagos, November 12th
Bot: [Searches and shows results]

You: Are there any morning flights?
Bot: Looking at the options, Option 1 (7:30 AM) and Option 3 (9:00 AM)
     are morning flights. Option 1 gets you there earliest!
```

## 🎯 Supported Questions

### About Results
- "Which is cheapest/fastest/best?"
- "What do you recommend?"
- "Compare the options"
- "Tell me about option [number]"
- "Any morning/afternoon/evening flights?"
- "Which airline is best?"

### Search Variations
- Single date: "Lagos to Abuja on Nov 15"
- Date range: "Lagos to Abuja from Nov 10 to Nov 17"
- Flexible: "Find me a cheap flight to Abuja next week"
- Natural: "I need to get to Port Harcourt tomorrow"

## 🧠 AI Features

### Without OpenAI Credits
If you haven't added OpenAI credits yet, the chat still works with:
- ✅ Regex-based parsing (finds cities, dates)
- ✅ Basic cheapest/fastest/best analysis
- ✅ All booking functionality

### With OpenAI Credits
Get the full conversational experience:
- ✅ Natural language understanding
- ✅ Smart intent detection
- ✅ Detailed flight analysis
- ✅ Personalized recommendations
- ✅ Contextual responses

## 🚀 Usage Tips

### Best Practices
1. **Be conversational** - Talk naturally, the AI understands!
2. **Ask questions** - Don't just pick the first option, discuss it
3. **Use date ranges** - Save money by finding the cheapest day
4. **Follow recommendations** - The AI balances price and convenience

### Power User Tips
```
# Find absolute cheapest
"Search Lagos to Abuja from Nov 1 to Nov 7, which day is cheapest?"

# Compare airlines
"Show me all airlines for this route and their prices"

# Flexible dates
"I'm flexible on dates, when is cheapest this month?"

# Quick booking
"Book the cheapest flight from Lagos to Abuja tomorrow"
```

## 🛠️ Technical Details

### AI Models Used
- **OpenAI GPT-3.5-turbo** for natural language understanding
- **Intent detection** for routing conversations
- **Flight analysis** for price/time optimization

### Fallback Mode
If OpenAI API fails:
- Switches to regex-based parsing
- Basic keyword matching
- Still fully functional!

### Session Management
- Remembers your search context
- Tracks conversation flow
- Maintains booking state

## 📊 What The AI Analyzes

When you ask "which is best?", the AI considers:
1. **Price** - Lower is better
2. **Duration** - Faster is better
3. **Departure time** - Convenience matters
4. **Airline** - Reliability counts
5. **Your preferences** - From conversation context

## 🎨 Customization

You can adjust the AI's personality in `app/chat/ai_assistant.py`:

```python
self.system_prompt = """You are a helpful and friendly flight booking assistant...
```

Change it to be:
- More formal/casual
- Budget-focused
- Speed-focused
- Family-friendly
- Business-oriented

## 🔧 Troubleshooting

### AI not understanding?
- **Check OpenAI credits**: https://platform.openai.com/account/billing
- **Check logs**: Look for `ai_intent_error` or `ai_analysis_error`
- **Fallback works**: Even without AI, basic search works!

### Wrong recommendations?
- AI might need more flight data to analyze
- Try asking more specific questions
- Provide feedback by rephrasing

## 📈 Future Enhancements

Coming soon:
- ✈️ Multi-city trips
- 🏨 Hotel recommendations
- 🚗 Car rental suggestions
- 💼 Corporate travel features
- 🎫 Loyalty program integration

## 💡 Pro Tips

**Save Money:**
```
"Find the cheapest flights from Lagos to Abuja in the next 2 weeks"
```

**Save Time:**
```
"What's the fastest way to get to Port Harcourt tomorrow morning?"
```

**Best Value:**
```
"I want a good balance of price and speed to Kano next week"
```

---

## 🎉 Start Chatting!

Open: **http://localhost:8001/chat**

Or share: **https://unopiated-michel-magically.ngrok-free.dev/chat**

Just start talking naturally - the AI will understand! 🤖✈️
