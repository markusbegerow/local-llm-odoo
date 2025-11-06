# -*- coding: utf-8 -*-
import json
import logging
import requests
import re
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

# Constants for validation
MAX_MESSAGE_LENGTH = 10000
MAX_MESSAGES_PER_MINUTE = 20


class LLMController(http.Controller):

    @http.route('/llm/chat', type='json', auth='user')
    def chat(self, conversation_id, message, **kwargs):
        """
        Handle chat requests from the frontend

        :param conversation_id: ID of the conversation (or False for new)
        :param message: User message content
        :return: Assistant response
        """
        try:
            # Input validation
            if not message or not isinstance(message, str):
                _logger.warning('Invalid message format from user %s', request.env.user.id)
                return {'error': 'Invalid message format'}

            message = message.strip()

            if not message:
                return {'error': 'Message cannot be empty'}

            if len(message) > MAX_MESSAGE_LENGTH:
                _logger.warning('Message too long from user %s: %d characters',
                               request.env.user.id, len(message))
                return {'error': f'Message too long. Maximum {MAX_MESSAGE_LENGTH} characters allowed'}

            # Rate limiting check
            if not self._check_rate_limit():
                _logger.warning('Rate limit exceeded for user %s', request.env.user.id)
                return {'error': 'Too many requests. Please wait a moment and try again'}

            # Get or create conversation
            Conversation = request.env['llm.conversation']
            Message = request.env['llm.message']

            if conversation_id:
                conversation = Conversation.browse(conversation_id)
                # Security check: ensure user owns this conversation
                if not conversation.exists():
                    _logger.warning('Conversation %s not found for user %s',
                                   conversation_id, request.env.user.id)
                    return {'error': 'Conversation not found'}

                if conversation.user_id.id != request.env.user.id:
                    _logger.error('Unauthorized access attempt to conversation %s by user %s',
                                 conversation_id, request.env.user.id)
                    return {'error': 'Unauthorized access'}
            else:
                # Create new conversation
                config = self._get_default_config()
                if not config:
                    _logger.error('No LLM configuration found for user %s', request.env.user.id)
                    return {
                        'error': 'No LLM configuration found. Please configure an LLM first.'
                    }

                conversation = Conversation.create({
                    'name': 'New Conversation',
                    'config_id': config.id,
                    'user_id': request.env.user.id,
                })
                _logger.info('Created new conversation %s for user %s',
                            conversation.id, request.env.user.id)

            # Create user message
            Message.create({
                'conversation_id': conversation.id,
                'role': 'user',
                'content': message,
            })

            # Prepare messages for API
            messages = self._prepare_messages(conversation)

            # Call LLM API
            response_content = self._call_llm_api(conversation.config_id, messages)

            if isinstance(response_content, dict) and 'error' in response_content:
                _logger.error('LLM API error for conversation %s: %s',
                             conversation.id, response_content['error'])
                return response_content

            # Create assistant message
            Message.create({
                'conversation_id': conversation.id,
                'role': 'assistant',
                'content': response_content,
            })

            # Update conversation name if it's the first exchange
            if conversation.message_count == 2 and conversation.name == 'New Conversation':
                conversation.name = message[:50] + '...' if len(message) > 50 else message

            _logger.info('Successfully processed message for conversation %s', conversation.id)
            return {
                'conversation_id': conversation.id,
                'response': response_content,
            }

        except AccessError as e:
            _logger.error('Access error in chat endpoint: %s', str(e), exc_info=True)
            return {'error': 'Access denied'}
        except ValidationError as e:
            _logger.warning('Validation error in chat endpoint: %s', str(e))
            return {'error': 'Invalid data provided'}
        except Exception as e:
            _logger.error('Unexpected error in chat endpoint: %s', str(e), exc_info=True)
            return {'error': 'An unexpected error occurred. Please try again later'}

    @http.route('/llm/stream_chat', type='json', auth='user')
    def stream_chat(self, conversation_id, message, **kwargs):
        """
        Handle streaming chat requests (for future implementation)
        """
        # TODO: Implement streaming using Server-Sent Events or websockets
        return self.chat(conversation_id, message, **kwargs)

    @http.route('/llm/conversations', type='json', auth='user')
    def get_conversations(self, **kwargs):
        """
        Get user's conversations
        """
        try:
            Conversation = request.env['llm.conversation']
            conversations = Conversation.search([
                ('user_id', '=', request.env.user.id),
                ('active', '=', True)
            ], order='write_date desc', limit=50)

            _logger.info('Loaded %d conversations for user %s',
                        len(conversations), request.env.user.id)

            return {
                'conversations': [{
                    'id': conv.id,
                    'name': conv.name,
                    'message_count': conv.message_count,
                    'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else None,
                } for conv in conversations]
            }
        except Exception as e:
            _logger.error('Error loading conversations for user %s: %s',
                         request.env.user.id, str(e), exc_info=True)
            return {'error': 'Failed to load conversations. Please try again'}

    @http.route('/llm/conversation/<int:conversation_id>/messages', type='json', auth='user')
    def get_messages(self, conversation_id, **kwargs):
        """
        Get messages for a specific conversation
        """
        try:
            Conversation = request.env['llm.conversation']
            conversation = Conversation.browse(conversation_id)

            if not conversation.exists():
                _logger.warning('Conversation %s not found for user %s',
                               conversation_id, request.env.user.id)
                return {'error': 'Conversation not found'}

            if conversation.user_id.id != request.env.user.id:
                _logger.error('Unauthorized access attempt to conversation %s by user %s',
                             conversation_id, request.env.user.id)
                return {'error': 'Unauthorized access'}

            _logger.info('Loaded %d messages for conversation %s',
                        len(conversation.message_ids), conversation_id)

            return {
                'messages': [{
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'create_date': msg.create_date.isoformat() if msg.create_date else None,
                } for msg in conversation.message_ids]
            }
        except Exception as e:
            _logger.error('Error loading messages for conversation %s: %s',
                         conversation_id, str(e), exc_info=True)
            return {'error': 'Failed to load messages. Please try again'}

    def _check_rate_limit(self):
        """
        Check if user has exceeded rate limit
        Uses Odoo's built-in session management for simplicity
        For production, consider Redis or memcached for distributed rate limiting
        """
        try:
            user_id = request.env.user.id
            session = request.session

            # Initialize rate limit tracking
            if 'llm_requests' not in session:
                session['llm_requests'] = []

            # Clean old requests (older than 1 minute)
            import time
            current_time = time.time()
            session['llm_requests'] = [
                req_time for req_time in session['llm_requests']
                if current_time - req_time < 60
            ]

            # Check rate limit
            if len(session['llm_requests']) >= MAX_MESSAGES_PER_MINUTE:
                return False

            # Add current request
            session['llm_requests'].append(current_time)
            return True

        except Exception as e:
            _logger.error('Error in rate limiting: %s', str(e), exc_info=True)
            # On error, allow the request through (fail open)
            return True

    def _get_default_config(self):
        """Get the default LLM configuration for the current user"""
        Config = request.env['llm.config']

        # Try to find user-specific default config
        config = Config.search([
            ('user_id', '=', request.env.user.id),
            ('is_default', '=', True),
            ('active', '=', True)
        ], limit=1)

        # If not found, try system default
        if not config:
            config = Config.search([
                ('user_id', '=', False),
                ('is_default', '=', True),
                ('active', '=', True)
            ], limit=1)

        # If still not found, get any active config
        if not config:
            config = Config.search([('active', '=', True)], limit=1)

        return config

    def _prepare_messages(self, conversation):
        """
        Prepare messages for LLM API call

        :param conversation: llm.conversation record
        :return: List of message dicts
        """
        config = conversation.config_id
        messages = []

        # Add system message
        if config.system_prompt:
            messages.append({
                'role': 'system',
                'content': config.system_prompt
            })

        # Add conversation messages (limit by max_history_messages)
        conversation_messages = conversation.message_ids.sorted('create_date')
        if len(conversation_messages) > config.max_history_messages:
            conversation_messages = conversation_messages[-config.max_history_messages:]

        for msg in conversation_messages:
            messages.append({
                'role': msg.role,
                'content': msg.content
            })

        return messages

    def _call_llm_api(self, config, messages):
        """
        Call the LLM API

        :param config: llm.config record
        :param messages: List of message dicts
        :return: Response content or error dict
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {config.api_token}'
            }

            data = {
                'model': config.model_name,
                'messages': messages,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
            }

            _logger.debug('Calling LLM API: %s with model %s', config.api_url, config.model_name)

            response = requests.post(
                config.api_url,
                headers=headers,
                json=data,
                timeout=config.request_timeout / 1000  # Convert ms to seconds
            )

            if response.status_code == 200:
                result = response.json()
                # Handle OpenAI-compatible response format
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    _logger.debug('LLM API call successful, response length: %d', len(content))
                    return content
                else:
                    _logger.error('Unexpected API response format from %s: %s',
                                 config.api_url, result)
                    return {'error': 'Unexpected response from LLM server'}
            else:
                _logger.error('LLM API error %s: %s', response.status_code, response.text[:200])
                # Don't expose detailed error to user
                return {
                    'error': f'LLM server returned error (status {response.status_code}). Please try again or contact support.'
                }

        except requests.exceptions.Timeout as e:
            _logger.warning('LLM API timeout for config %s: %s', config.id, str(e))
            return {'error': 'Request timeout. The LLM took too long to respond. Please try again.'}
        except requests.exceptions.ConnectionError as e:
            _logger.error('LLM connection error for config %s: %s', config.id, str(e))
            return {'error': 'Cannot connect to LLM server. Please check the configuration.'}
        except requests.exceptions.RequestException as e:
            _logger.error('LLM request error for config %s: %s', config.id, str(e), exc_info=True)
            return {'error': 'Error communicating with LLM server. Please try again.'}
        except Exception as e:
            _logger.error('Unexpected error calling LLM API: %s', str(e), exc_info=True)
            return {'error': 'An unexpected error occurred. Please try again later.'}
