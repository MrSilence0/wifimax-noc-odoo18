{
    'name': 'Wifimax NOC AI',
    'version': '1.0',
    'summary': 'Sistema NOC con IA para monitoreo y tickets',
    'author': 'Wifimax',
    'category': 'Operations',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/noc_ticket_views.xml',
    ],
    'installable': True,
    'application': True,
}