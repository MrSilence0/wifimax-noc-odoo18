{
    'name': 'Wifimax NOC AI',
    'version': '1.0',
    'summary': 'Sistema NOC con IA para monitoreo y tickets',
    'author': 'Wifimax',
    'category': 'Operations',
    'depends': ['base', 'mail'],
    'data': [

        'security/noc_security.xml',
        'security/ir.model.access.csv',
        'security/noc_record_rules.xml',

        'data/noc_sequence.xml',
        'data/cron.xml',
        'data/mail_template.xml',
        
        'views/noc_ticket_views.xml',
        'views/noc_ticket_graph_views.xml',
        'views/noc_ticket_pivot_views.xml',
    ],
    'installable': True,
    'application': True,
}