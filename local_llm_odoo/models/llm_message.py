# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LLMMessage(models.Model):
    _name = 'llm.message'
    _description = 'LLM Message'
    _order = 'create_date asc, id asc'

    conversation_id = fields.Many2one('llm.conversation', string='Conversation', required=True, ondelete='cascade')
    role = fields.Selection([
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], string='Role', required=True)
    content = fields.Text(string='Content', required=True)
    create_date = fields.Datetime(string='Created On', readonly=True)
    tokens_used = fields.Integer(string='Tokens Used', help='Approximate number of tokens in this message')

    @api.model
    def create(self, vals):
        """Calculate tokens on message creation"""
        message = super().create(vals)
        if message.content:
            # Simple token estimation: ~4 characters per token
            message.tokens_used = len(message.content) // 4
        return message
