from openerp import api, models, fields

class planner_planner(models.Model):
    _name = 'planner.planner'

    name = fields.Char('Name', required=True)
    menu_id = fields.Many2one('ir.ui.menu', 'Menu', required=True)
    view_id = fields.Many2one('ir.ui.view', 'Template', required=True)
    progress = fields.Integer("Progress")
    data = fields.Text('Data')
    tooltip_planner = fields.Html('Planner Tooltips', translate=True)

