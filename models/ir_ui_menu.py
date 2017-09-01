# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright TUANNA7593@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api, SUPERUSER_ID


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    invis_groups_ids = fields.Many2many(
        'res.groups', 'menu_invisible_group_rel',
        'menu_id', 'group_id', 'Invisible Groups')

    @api.multi
    @api.returns('self')
    def _filter_visible_menus(self):
        visible = super(IrUiMenu, self)._filter_visible_menus()
        groups = self.env.user.groups_id
        if self._uid != SUPERUSER_ID:
            visible = [menu for menu in visible
                       if not any(group in groups
                                  for group in menu.invis_groups_ids)]
        return self.filtered(lambda menu: menu in visible)
