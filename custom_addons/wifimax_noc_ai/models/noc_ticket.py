from datetime import timedelta
from odoo import models, fields, api
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class NocTicket(models.Model):
    _name = 'wifimax.noc.ticket'
    _description = 'NOC Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Ticket',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )

    description = fields.Text(
        string='Descripción'
    )

    status = fields.Selection([
        ('1_new', 'Nuevo'),
        ('2_progress', 'En Progreso'),
        ('3_done', 'Resuelto')
    ],
        default='1_new',
        string='Estado',
        tracking=True
    )

    priority = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta')
    ],
        default='medium',
        string='Prioridad',
        tracking=True
    )

    severity = fields.Selection(
        [
            ('info', 'Informativo'),
            ('warning', 'Advertencia'),
            ('critical', 'Crítico')
        ],
        string='Severidad',
        compute='_compute_severity',
        store=True,
        tracking=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        tracking=True
    )

    assigned_user_id = fields.Many2one(
        'res.users',
        string='Técnico Asignado',
        tracking=True
    )

    device_ip = fields.Char(
        string='IP Equipo'
    )

    detection_date = fields.Datetime(
        string='Fecha Detección',
        default=fields.Datetime.now
    )

    close_date = fields.Datetime(
        string='Fecha Resolución',
        tracking=True
    )

    sla_deadline = fields.Datetime(
        string='SLA Deadline'
    )

    sla_hours = fields.Float(
        string='Horas SLA',
        compute='_compute_sla_hours',
        store=True
    )

    sla_status = fields.Selection(
        selection=[
            ('ok', 'Dentro SLA'),
            ('warning', 'Por vencer'),
            ('expired', 'Vencido')
        ],
        string='SLA Status',
        compute='_compute_sla_status',
        store=True,
        tracking=True
    )
    
    ticket_count = fields.Integer(
        string='Tickets',
        default=1
    )

    @api.depends('sla_deadline')
    def _compute_sla_status(self):

        for rec in self:

            if not rec.sla_deadline:
                rec.sla_status = 'ok'
                continue

            now = fields.Datetime.now()
            remaining = rec.sla_deadline - now
            hours_left = remaining.total_seconds() / 3600

            if hours_left <= 0:
                rec.sla_status = 'expired'

            elif hours_left <= 1:
                rec.sla_status = 'warning'

            else:
                rec.sla_status = 'ok'

    @api.depends('priority', 'sla_status')
    def _compute_severity(self):

        for rec in self:

            # SLA vencido = crítico
            if rec.sla_status == 'expired':
                rec.severity = 'critical'

            # Prioridad alta = crítico
            elif rec.priority == 'high':
                rec.severity = 'critical'

            # SLA por vencer = warning
            elif rec.sla_status == 'warning':
                rec.severity = 'warning'

            # Todo lo demás = informativo
            else:
                rec.severity = 'info'

    def action_start_progress(self):
        self.status = '2_progress'

    def action_done(self):

        self.status = '3_done'

        self.close_date = fields.Datetime.now()

        template = self.env.ref(
            'wifimax_noc_ai.email_template_noc_ticket_done',
            raise_if_not_found=False
        )

        if template and self.partner_id.email:

            template.send_mail(
                self.id,
                force_send=True
            )

    def action_reset(self):
        self.status = '1_new'

    @api.model
    def create(self, vals):

        if vals.get('name', 'Nuevo') == 'Nuevo':

            vals['name'] = self.env['ir.sequence'].next_by_code(
                'wifimax.noc.ticket'
            ) or 'NOC-0000'

        rec = super().create(vals)

        # =========================
        # SLA
        # =========================

        if rec.priority == 'high':

            rec.sla_deadline = (
                fields.Datetime.now() + timedelta(hours=1)
            )

            _logger.warning(
                f'Ticket crítico creado: {rec.name}'
            )

        elif rec.priority == 'medium':

            rec.sla_deadline = (
                fields.Datetime.now() + timedelta(hours=4)
            )

        else:

            rec.sla_deadline = (
                fields.Datetime.now() + timedelta(hours=8)
            )

        # =========================
        # EMAIL CREATED
        # =========================

        template = self.env.ref(
            'wifimax_noc_ai.email_template_noc_ticket_created',
            raise_if_not_found=False
        )

        if template and rec.partner_id.email:

            template.send_mail(
                rec.id,
                force_send=True
            )

        return rec
    
    def check_sla_warning(self):

        tickets = self.search([
            ('sla_status', '=', 'warning'),
            ('status', '!=', '3_done')
        ])

        activity_type = self.env.ref(
            'mail.mail_activity_data_todo'
        )

        for rec in tickets:

            if not rec.assigned_user_id:
                continue

            # Evitar actividades duplicadas
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id),
                ('activity_type_id', '=', activity_type.id),
                ('user_id', '=', rec.assigned_user_id.id),
                ('summary', '=', 'SLA Warning')
            ], limit=1)

            if existing_activity:
                continue

            rec.activity_schedule(
                activity_type.id,
                user_id=rec.assigned_user_id.id,
                summary='SLA Warning',
                note='El ticket está por vencer SLA.'
            )

        # =========================
        # SLA EXPIRED EMAIL
        # =========================

        expired_tickets = self.search([
            ('sla_status', '=', 'expired'),
            ('status', '!=', '3_done')
        ])

        template = self.env.ref(
            'wifimax_noc_ai.email_template_noc_sla_expired',
            raise_if_not_found=False
        )

        for rec in expired_tickets:

            if template and rec.partner_id.email:

                template.send_mail(
                    rec.id,
                    force_send=True
                )
            
    def get_open_tickets_count(self):
        return self.search_count([
            ('status', '!=', '3_done')
        ])

    def get_critical_tickets_count(self):
        return self.search_count([
            ('severity', '=', 'critical')
        ])

    def get_expired_sla_count(self):
        return self.search_count([
            ('sla_status', '=', 'expired')
        ])

    def get_resolved_tickets_count(self):
        return self.search_count([
            ('status', '=', '3_done')
        ])
    
    @api.depends('detection_date', 'close_date')
    def _compute_sla_hours(self):

        for rec in self:

            if rec.detection_date and rec.close_date:

                delta = rec.close_date - rec.detection_date

                rec.sla_hours = delta.total_seconds() / 3600

            else:
                rec.sla_hours = 0