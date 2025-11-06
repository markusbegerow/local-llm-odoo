# Local LLM Odoo Module

A powerful Odoo 18 module that integrates local Large Language Models (LLMs) directly into your Odoo ERP system for AI-powered assistance.

<img alt="image" src="https://github.com/markusbegerow/local-llm-odoo/blob/d1f0183252624764d8034d008f1675cdd8316a75/static/description/banner.png?raw=true" />

## Features

### 🤖 Local AI Integration
- **Privacy-First**: All data stays on your server—no cloud APIs required
- **Multiple LLM Support**: Works with Ollama, LM Studio, vLLM, and OpenAI-compatible endpoints
- **Persistent Conversations**: Chat history is maintained and stored in Odoo database
- **Real-time Chat**: Interactive chat interface integrated into Odoo backend

### 🔒 Enterprise-Grade Security
- **API Token Encryption**: All API tokens encrypted at rest using Fernet (AES-128)
- **CSRF Protection**: Full Cross-Site Request Forgery protection on all endpoints
- **Rate Limiting**: Configurable rate limits (default: 20 requests/minute per user)
- **Input Validation**: Comprehensive validation and sanitization of all user inputs
- **Record-Level Security**: Database-enforced access control - users can only see their own data
- **Audit Logging**: Complete logging of all security events and user actions
- **Error Sanitization**: Safe error messages that don't leak system information

### 🎯 Core Functionality
- **Configuration Management**: Multiple LLM configurations (system-wide or user-specific)
- **Conversation History**: Track and manage all AI conversations
- **Message Storage**: All messages stored in database with timestamps
- **Test Connection**: Built-in tool to verify LLM server connectivity
- **Flexible Settings**: Configure temperature, max tokens, system prompts, and more

### 💼 Business Use Cases
- Product description generation
- Email drafting assistance
- Customer service support
- Data analysis and insights
- Report generation
- General business automation

## Requirements

- **Odoo**: Version 18.0
- **Python**: 3.10+
- **Python Packages**:
  - `requests>=2.31.0` - HTTP client for LLM API calls
  - `cryptography>=41.0.0` - API token encryption
  - `urllib3>=2.0.0` - Connection pooling support
- **Local LLM Server**: One of:
  - Ollama (recommended)
  - LM Studio
  - vLLM
  - Any OpenAI-compatible API endpoint

## Installation

### 1. Set Up Your Local LLM Server

#### Option A: Ollama (Recommended)
```bash
# Install Ollama from https://ollama.ai
# Pull a model
ollama pull llama3.2

# Start the server (usually runs automatically)
ollama serve
```

#### Option B: LM Studio
1. Download from [lmstudio.ai](https://lmstudio.ai)
2. Load a model
3. Start the local server (default: `http://localhost:1234`)

### 2. Install Python Dependencies

```bash
# Navigate to the module directory
cd local_llm_odoo

# Install required Python packages
pip install -r requirements.txt

# Or install manually
pip install requests>=2.31.0 cryptography>=41.0.0 urllib3>=2.0.0
```

### 3. Install the Odoo Module

```bash
# Copy the module to your Odoo addons directory
cp -r local_llm_odoo /path/to/odoo/addons/

# Or create a symlink
ln -s /path/to/local_llm_odoo /path/to/odoo/addons/

# Restart Odoo server
sudo systemctl restart odoo
# or
python3 odoo-bin -c odoo.conf
```

### 4. Activate the Module in Odoo

1. Go to **Apps** menu
2. Remove the "Apps" filter
3. Search for "Local LLM"
4. Click **Install**

## Configuration

### Initial Setup

1. Go to **Local LLM** → **Configuration** → **LLM Settings**
2. The module comes with a default Ollama configuration
3. Click **Test Connection** to verify it works
4. Adjust settings as needed:
   - **API URL**: Your LLM server endpoint
   - **Model Name**: The model to use (e.g., `llama3.2`, `mistral`)
   - **Temperature**: Response randomness (0.0-2.0)
   - **Max Tokens**: Maximum response length
   - **System Prompt**: Define AI behavior

### Multiple Configurations

You can create multiple LLM configurations for:
- Different models (coding vs. general purpose)
- Different servers (local vs. remote)
- User-specific settings
- Testing vs. production

### User-Specific Settings

- Leave **User** field empty for system-wide configuration
- Assign to specific user for personal settings
- Mark as **Default** to use automatically in new conversations

## Usage

### Starting a Conversation

1. Go to **Local LLM** → **Chat**
2. Click **Create** or use the chat widget
3. Type your message and press Enter
4. The AI will respond based on your configuration

### Managing Conversations

- View all conversations in list view
- Open any conversation to see message history
- Use **Clear Messages** to delete all messages in a conversation
- Archive old conversations to keep workspace clean

### Chat Widget (Future Feature)

The module includes a chat widget that can be integrated into any Odoo view for quick AI assistance.

## Architecture

### Models

- **llm.config**: LLM configuration settings
- **llm.conversation**: Conversation tracking
- **llm.message**: Individual messages in conversations

### Controllers

- `/llm/chat`: Send messages and get responses
- `/llm/conversations`: List user conversations
- `/llm/conversation/<id>/messages`: Get conversation messages
- `/llm/stream_chat`: Streaming responses (future)

### Security

**Access Control**:
- Role-based access control via Odoo security groups
- Record-level security rules enforced at database level
- Users can ONLY access their own conversations and messages
- System administrators have full access to all data
- Separate read/write permissions for configurations

**Data Protection**:
- API tokens encrypted at rest using Fernet (AES-128)
- Encryption keys stored in system parameters (should be moved to environment variables in production)
- Automatic encryption of new and existing tokens
- CSRF protection on all endpoints

**Input Validation & Sanitization**:
- Maximum message length: 10,000 characters
- Type checking and sanitization of all user inputs
- Protection against prompt injection attacks
- Safe error messages that don't expose system internals

**Rate Limiting**:
- Session-based rate limiting per user
- Default: 20 requests per minute
- Configurable in `controllers/main.py`
- Prevents API abuse and DoS attacks

**Audit & Logging**:
- Comprehensive logging of all security events
- Failed access attempts logged
- User actions tracked
- Detailed error logging for troubleshooting

## API Integration

### OpenAI-Compatible Format

The module uses the standard OpenAI API format:

```python
POST /v1/chat/completions
{
    "model": "llama3.2",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}
```

### Supported Endpoints

- **Ollama**: `http://localhost:11434/v1/chat/completions`
- **LM Studio**: `http://localhost:1234/v1/chat/completions`
- **vLLM**: `http://localhost:8000/v1/chat/completions`
- **Custom**: Any OpenAI-compatible endpoint

## Troubleshooting

### Connection Issues

**Error**: "Connection error. Please check if the LLM server is running."

**Solution**:
```bash
# For Ollama
curl http://localhost:11434/api/tags

# For LM Studio
curl http://localhost:1234/v1/models

# Check if service is running
ps aux | grep ollama
```

### Timeout Issues

**Error**: "Request timeout. The LLM took too long to respond."

**Solution**:
1. Increase **Request Timeout** in configuration (default: 120000ms)
2. Use a smaller/faster model
3. Reduce **Max Tokens** setting

### API Format Issues

**Error**: "Unexpected API response format"

**Solution**:
- Verify your endpoint uses OpenAI-compatible format
- Check API documentation for your LLM server
- Test endpoint with curl:
```bash
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Rate Limiting Issues

**Error**: "Too many requests. Please wait a moment and try again"

**Solution**:
1. Default limit is 20 messages per minute per user
2. Wait 60 seconds and try again
3. To adjust the limit, edit `controllers/main.py`:
   ```python
   MAX_MESSAGES_PER_MINUTE = 50  # Change to desired limit
   ```
4. Restart Odoo after making changes

### Permission/Access Issues

**Error**: "Conversation not found" or "Unauthorized access"

**Solution**:
1. Users can only access their own conversations
2. Verify you're logged in as the correct user
3. System administrators have access to all conversations
4. Check Security Rules: **Settings** → **Technical** → **Record Rules** → Search "LLM"

### Encryption Issues

**Error**: Token decryption failures or "cryptography library not installed"

**Solution**:
```bash
# Install cryptography library
pip install cryptography>=41.0.0

# Restart Odoo
sudo systemctl restart odoo

# Check encryption key exists
# Settings → Technical → System Parameters → llm.encryption_key
```

## Development

### Module Structure

```
local_llm_odoo/
├── __init__.py
├── __manifest__.py
├── README.md
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── controllers/
│   ├── __init__.py
│   └── main.py             # HTTP controllers with security
├── models/
│   ├── __init__.py
│   ├── llm_config.py       # LLM configuration with encryption
│   ├── llm_conversation.py # Conversation model
│   └── llm_message.py      # Message model
├── views/
│   ├── llm_config_views.xml
│   ├── llm_conversation_views.xml
│   └── llm_menu_views.xml
├── security/
│   ├── ir.model.access.csv      # Access control lists
│   └── llm_security_rules.xml   # Record-level security rules
├── data/
│   └── llm_config_data.xml      # Default configurations
└── static/
    └── src/
        ├── js/
        │   └── llm_chat_widget.js
        ├── xml/
        │   └── llm_chat_templates.xml
        └── css/
            └── llm_chat.css
```

### Adding New Features

1. **Streaming Responses**: Implement SSE in controller
2. **File Upload**: Allow users to send files to LLM
3. **RAG Integration**: Connect to document search
4. **Multi-Modal**: Add image understanding
5. **Voice Input**: Speech-to-text integration

## Recommended Models

### For Coding Tasks
- **Llama 3.2 8B**: Fast, good for general coding
- **CodeLlama 13B**: Specialized for code generation
- **Qwen 2.5 Coder**: Excellent code understanding
- **DeepSeek Coder**: Strong at algorithms

### For Business Tasks
- **Llama 3.2**: Best all-around
- **Mistral 7B**: Fast and efficient
- **Phi-3**: Compact but capable

## Security Best Practices

### ✅ Built-in Security Features

- **Data Privacy**: All data stays on your server - no external API calls
- **Encryption**: API tokens encrypted at rest using Fernet (AES-128)
- **Access Control**: Database-enforced record-level security rules
- **CSRF Protection**: Full protection against cross-site request forgery
- **Rate Limiting**: Protection against API abuse (20 requests/min default)
- **Input Validation**: Comprehensive validation and sanitization
- **Audit Logging**: Complete logging of security events and user actions
- **Conversation Isolation**: Users can only access their own data

### ⚠️ Production Deployment Checklist

**Before Going Live**:

1. **Secure the Encryption Key**:
   ```bash
   # Extract encryption key from Odoo
   # Settings → Technical → System Parameters → llm.encryption_key

   # Store in environment variable (recommended)
   export LLM_ENCRYPTION_KEY="your-key-here"

   # Or use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
   ```

2. **Network Security**:
   - ✅ Ensure LLM server is NOT exposed to the internet
   - ✅ Use firewall rules to restrict LLM server access
   - ✅ Run Odoo behind a reverse proxy (nginx/Apache)
   - ✅ Enable HTTPS with valid SSL certificates
   - ✅ Consider VPN for remote LLM server access

3. **Database Security**:
   - ✅ Regular automated backups (at least daily)
   - ✅ Test backup restoration procedure
   - ✅ Enable PostgreSQL authentication
   - ✅ Restrict database access to localhost
   - ✅ Use strong database passwords

4. **API Token Management**:
   - ✅ Use strong, unique API tokens for production
   - ✅ Rotate tokens periodically (every 90 days recommended)
   - ✅ Don't use default tokens like "ollama" in production
   - ✅ Store tokens securely (never in version control)

5. **Monitoring & Logging**:
   - ✅ Set up log aggregation (ELK, Splunk, etc.)
   - ✅ Monitor for security events (failed access, rate limits)
   - ✅ Set up alerts for critical errors
   - ✅ Review logs regularly for suspicious activity

6. **System Hardening**:
   - ✅ Keep Odoo and dependencies updated
   - ✅ Run Odoo as non-root user
   - ✅ Disable unnecessary Odoo modules
   - ✅ Configure proper file permissions
   - ✅ Enable SELinux/AppArmor if available

7. **Rate Limiting (Optional - Advanced)**:
   - For high-traffic environments, implement Redis-based rate limiting
   - Configure per-user and per-IP rate limits
   - Set up DDoS protection at reverse proxy level

### 🔐 Compliance Considerations

- **GDPR**: User data is stored in your database - ensure proper data handling procedures
- **Data Retention**: Implement conversation cleanup policies if required
- **User Privacy**: Consider allowing users to delete their conversation history
- **Audit Trail**: All security events are logged for compliance auditing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check Odoo community forums
- Review LLM server documentation

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Ollama team for making local LLMs accessible
- Odoo SA for the excellent ERP framework
- LM Studio for local inference platform

## 🙋‍♂️ Get Involved

If you encounter any issues or have questions:
- 🐛 [Report bugs](https://github.com/markusbegerow/local-llm-odoo/issues)
- 💡 [Request features](https://github.com/markusbegerow/local-llm-odoo/issues)
- ⭐ Star the repo if you find it useful!

## ☕ Support the Project

If you like this project, support further development with a repost or coffee:

<a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/MarkusBegerow/local-llm-odoo" target="_blank"> <img src="https://img.shields.io/badge/💼-Share%20on%20LinkedIn-blue" /> </a>

[![Buy Me a Coffee](https://img.shields.io/badge/☕-Buy%20me%20a%20coffee-yellow)](https://paypal.me/MarkusBegerow?country.x=DE&locale.x=de_DE)

## 📬 Contact

- 🧑‍💻 [Markus Begerow](https://linkedin.com/in/markusbegerow)
- 💾 [GitHub](https://github.com/markusbegerow)
- ✉️ [Twitter](https://x.com/markusbegerow)

---

**Privacy Notice**: This extension operates entirely locally. No data is sent to external servers unless you explicitly configure it to use a remote API endpoint.
