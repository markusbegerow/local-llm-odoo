# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LLMConversation(models.Model):
    _name = 'llm.conversation'
    _description = 'LLM Conversation'
    _order = 'write_date desc, id desc'

    name = fields.Char(string='Conversation Title', required=True, default='New Conversation')
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    config_id = fields.Many2one('llm.config', string='LLM Configuration', required=True)
    message_ids = fields.One2many('llm.message', 'conversation_id', string='Messages')
    message_count = fields.Integer(string='Message Count', compute='_compute_message_count', store=True)
    last_message_date = fields.Datetime(string='Last Message', compute='_compute_last_message_date', store=True)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)

    @api.depends('message_ids.create_date')
    def _compute_last_message_date(self):
        for record in self:
            if record.message_ids:
                record.last_message_date = max(record.message_ids.mapped('create_date'))
            else:
                record.last_message_date = False

    @api.model
    def create(self, vals):
        """Auto-generate conversation name from first message if not provided"""
        conversation = super().create(vals)
        if conversation.name == 'New Conversation' and conversation.message_ids:
            first_user_msg = conversation.message_ids.filtered(lambda m: m.role == 'user')
            if first_user_msg:
                content = first_user_msg[0].content
                conversation.name = content[:50] + '...' if len(content) > 50 else content
        return conversation

    def clear_messages(self):
        """Clear all messages in the conversation"""
        self.ensure_one()
        self.message_ids.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Conversation Cleared'),
                'message': _('All messages have been deleted.'),
                'type': 'success',
                'sticky': False,
            }
        }
