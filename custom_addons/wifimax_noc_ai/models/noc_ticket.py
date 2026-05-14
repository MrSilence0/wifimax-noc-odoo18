from odoo import models, fields

class NocTicket(models.Model):
    _name = 'wifimax.noc.ticket'
    _description = 'NOC Ticket'

    name = fields.Char(string='Ticket', required=True)
    description = fields.Text(string='Descripción')
    status = fields.Selection([
        ('new', 'Nuevo'),
        ('progress', 'En Progreso'),
        ('done', 'Resuelto')
    ], default='new', string='Estado')

    client_name = fields.Char(string='Cliente')
    device_ip = fields.Char(string='IP Equipo')
    detection_date = fields.Datetime(
        string='Fecha Detección',
        default=fields.Datetime.now
    )