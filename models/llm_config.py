# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LLMConfig(models.Model):
    _name = 'llm.config'
    _description = 'LLM Configuration'
    _order = 'sequence, id'

    name = fields.Char(string='Configuration Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # API Configuration
    api_url = fields.Char(
        string='API URL',
        required=True,
        default='http://localhost:11434/v1/chat/completions',
        help='Full API endpoint URL (e.g., http://localhost:11434/v1/chat/completions for Ollama)'
    )
    api_token_encrypted = fields.Char(
        string='API Token (Encrypted)',
        help='Encrypted API authentication token - DO NOT EDIT DIRECTLY'
    )
    api_token = fields.Char(
        string='API Token',
        compute='_compute_api_token',
        inverse='_inverse_api_token',
        default='ollama',
        help='API authentication token (use "ollama" for Ollama, or your API key for other services)'
    )

    # Model Configuration
    model_name = fields.Char(
        string='Model Name',
        required=True,
        default='llama3.2',
        help='Name of the model to use (e.g., llama3.2, mistral, codellama)'
    )
    temperature = fields.Float(
        string='Temperature',
        default=0.7,
        help='Sampling temperature (0.0 = deterministic, 2.0 = very random)'
    )
    max_tokens = fields.Integer(
        string='Max Tokens',
        default=2048,
        help='Maximum number of tokens in the response'
    )

    # System Configuration
    system_prompt = fields.Text(
        string='System Prompt',
        default='You are a helpful AI assistant integrated into Odoo ERP system. '
                'Help users with their tasks, answer questions, and provide insights based on their business data. '
                'Keep responses clear, concise, and professional.',
        help='System prompt that defines the AI behavior'
    )
    max_history_messages = fields.Integer(
        string='Max History Messages',
        default=50,
        help='Maximum number of messages to keep in conversation history'
    )
    request_timeout = fields.Integer(
        string='Request Timeout (ms)',
        default=120000,
        help='Request timeout in milliseconds (default: 120000 = 2 minutes)'
    )

    # Usage
    is_default = fields.Boolean(
        string='Default Configuration',
        help='Use this configuration as the default for new conversations'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        help='Leave empty for system-wide configuration, or select a user for user-specific settings'
    )

    def _get_encryption_key(self):
        """
        Get encryption key from system parameter
        In production, this should be stored securely (e.g., environment variable, secrets manager)
        """
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        key = IrConfigParam.get_param('llm.encryption_key')

        if not key:
            # Generate a new key if it doesn't exist
            try:
                from cryptography.fernet import Fernet
                key = Fernet.generate_key().decode()
                IrConfigParam.set_param('llm.encryption_key', key)
                _logger.warning('Generated new encryption key for LLM tokens. '
                              'For production, store this securely in environment variables.')
            except ImportError:
                _logger.error('cryptography library not installed. API tokens will not be encrypted.')
                return None

        return key

    def _encrypt_token(self, token):
        """Encrypt API token"""
        if not token:
            return False

        try:
            from cryptography.fernet import Fernet
            key = self._get_encryption_key()
            if not key:
                _logger.warning('Encryption key not available, storing token in plain text')
                return token

            f = Fernet(key.encode())
            encrypted = f.encrypt(token.encode())
            return encrypted.decode()
        except ImportError:
            _logger.warning('cryptography library not installed, storing token in plain text')
            return token
        except Exception as e:
            _logger.error('Error encrypting token: %s', str(e), exc_info=True)
            return token

    def _decrypt_token(self, encrypted_token):
        """Decrypt API token"""
        if not encrypted_token:
            return 'ollama'  # Default value

        try:
            from cryptography.fernet import Fernet
            key = self._get_encryption_key()
            if not key:
                return encrypted_token

            f = Fernet(key.encode())
            decrypted = f.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except ImportError:
            return encrypted_token
        except Exception as e:
            _logger.error('Error decrypting token: %s', str(e), exc_info=True)
            return encrypted_token

    @api.depends('api_token_encrypted')
    def _compute_api_token(self):
        """Decrypt token for display/use"""
        for record in self:
            if record.api_token_encrypted:
                record.api_token = record._decrypt_token(record.api_token_encrypted)
            else:
                record.api_token = 'ollama'

    def _inverse_api_token(self):
        """Encrypt token when set"""
        for record in self:
            if record.api_token:
                record.api_token_encrypted = record._encrypt_token(record.api_token)

    @api.constrains('temperature')
    def _check_temperature(self):
        for record in self:
            if not 0.0 <= record.temperature <= 2.0:
                raise ValidationError(_('Temperature must be between 0.0 and 2.0'))

    @api.constrains('max_tokens')
    def _check_max_tokens(self):
        for record in self:
            if record.max_tokens < 128 or record.max_tokens > 32768:
                raise ValidationError(_('Max tokens must be between 128 and 32768'))

    @api.constrains('is_default')
    def _check_default(self):
        """Ensure only one default configuration per user"""
        for record in self:
            if record.is_default:
                domain = [('is_default', '=', True), ('id', '!=', record.id)]
                if record.user_id:
                    domain.append(('user_id', '=', record.user_id.id))
                else:
                    domain.append(('user_id', '=', False))

                if self.search_count(domain) > 0:
                    raise ValidationError(_('Only one default configuration is allowed per user'))

    def test_connection(self):
        """Test the LLM API connection"""
        self.ensure_one()
        try:
            import requests
            import json

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_token}'
            }

            data = {
                'model': self.model_name,
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10,
                'temperature': 0.1
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connection successful! Model is responding.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Failed'),
                        'message': _(f'Error {response.status_code}: {response.text}'),
                        'type': 'danger',
                        'sticky': True,
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
