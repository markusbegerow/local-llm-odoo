# -*- coding: utf-8 -*-
{
    'name': 'Local LLM Chat',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Integrate Local LLMs (Ollama, LM Studio) into Odoo for AI-powered assistance with enterprise security',
    'description': """
        Local LLM Integration for Odoo 18
        ==================================

        Features:
        ---------
        * Chat with local LLMs directly in Odoo
        * Privacy-first: All data stays on your server
        * Support for Ollama, LM Studio, and OpenAI-compatible endpoints
        * AI-powered assistance for:
            - Product descriptions
            - Email drafting
            - Customer service
            - Data analysis
            - Report generation
        * Conversation history tracking
        * Configurable models and parameters
        * System-wide and user-specific settings

        Security Features:
        ------------------
        * API token encryption (AES-128)
        * CSRF protection on all endpoints
        * Rate limiting (20 req/min default)
        * Input validation and sanitization
        * Record-level security rules
        * Comprehensive audit logging
        * Safe error messages
    """,
    'author': 'Markus Begerow',
    'website': 'https://github.com/markusbegerow/local-llm-odoo',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/llm_security_rules.xml',
        'views/llm_config_views.xml',
        'views/llm_conversation_views.xml',
        'views/llm_menu_views.xml',
        'data/llm_config_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'local_llm_odoo/static/src/js/llm_chat_widget.js',
            'local_llm_odoo/static/src/xml/llm_chat_templates.xml',
            'local_llm_odoo/static/src/css/llm_chat.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
