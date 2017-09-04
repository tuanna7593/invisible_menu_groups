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

import misc
import logging
import os.path

from openerp.tools.convert import xml_import, convert_xml_import
from lxml import etree
from xml.dom import minidom
from xml.dom.minidom import Document

_logger = logging.getLogger(__name__)


def _tag_menuitem(self, rec, data_node=None, mode=None):
    rec_id = rec.get("id",'').encode('ascii')
    self._test_xml_id(rec_id)

    # The parent attribute was specified,
    # if non-empty determine its ID, otherwise
    # explicitly make a top-level menu
    if rec.get('parent'):
        menu_parent_id = self.id_get(cr, rec.get('parent',''))
    else:
        # we get here with <menuitem parent="">, explicit clear of parent, or
        # if no parent attribute at all but menu name is not a menu path
        menu_parent_id = False
    values = {'parent_id': menu_parent_id}
    if rec.get('name'):
        values['name'] = rec.get('name')
    try:
        res = [ self.id_get(cr, rec.get('id','')) ]
    except:
        res = None

    if rec.get('action'):
        a_action = rec.get('action','').encode('utf8')

        # determine the type of action
        action_type, action_id = self.model_id_get(cr, a_action)
        action_type = action_type.split('.')[-1] # keep only type part
        values['action'] = "ir.actions.%s,%d" % (action_type, action_id)

        if not values.get('name') and action_type in (
                        'act_window', 'wizard', 'url', 'client', 'server'):
            a_table = 'ir_act_%s' % action_type.replace('act_', '')
            cr.execute('select name from "%s" where id=%%s' % a_table,
                       (int(action_id),))
            resw = cr.fetchone()
            if resw:
                values['name'] = resw[0]

    if not values.get('name'):
        # ensure menu has a name
        values['name'] = rec_id or '?'

    if rec.get('sequence'):
        values['sequence'] = int(rec.get('sequence'))

    if rec.get('groups'):
        g_names = rec.get('groups','').split(',')
        groups_value = []
        for group in g_names:
            if group.startswith('-'):
                group_id = self.id_get(cr, group[1:])
                groups_value.append((3, group_id))
            else:
                group_id = self.id_get(cr, group)
                groups_value.append((4, group_id))
        values['groups_id'] = groups_value

    if rec.get('invisible_groups'):
        g_names = rec.get('invisible_groups', '').split(',')
        invis_groups_value = []
        for group in g_names:
            if group.startswith('-'):
                group_id = self.id_get(group[1:])
                invis_groups_value.append((3, group_id))
            else:
                group_id = self.id_get(group)
                invis_groups_value.append((4, group_id))
        values['invis_groups_ids'] = invis_groups_value

    if not values.get('parent_id'):
        if rec.get('web_icon'):
            values['web_icon'] = rec.get('web_icon')

    pid = self.pool['ir.model.data']._update(
            cr, self.uid, 'ir.ui.menu', self.module, values,
            rec_id, noupdate=self.isnoupdate(data_node),
            mode=self.mode, res_id=res and res[0] or False)

    if rec_id and pid:
        self.idref[rec_id] = int(pid)

    return 'ir.ui.menu', pid

xml_import._tag_menuitem = _tag_menuitem


def convert_xml_import(cr, module, xmlfile, idref=None, mode='init',
                       noupdate=False, report=None):
    doc = etree.parse(xmlfile)
    xdoc = Document()
    rng_doc = minidom.parse(
        os.path.join(config['root_path'], 'import_xml.rng'))
    rng_element_tags = rng_doc.getElementsByTagName('rng:element')
    for rng_element in rng_element_tags:
        attributes = dict(rng_element.attributes)
        if attributes.get('name', False) \
                and attributes['name'].value == 'menuitem':
            new_optional = xdoc.createElement('rng:optional')
            new_attribute = xdoc.createElement('rng:attribute')
            new_attribute.setAttribute('name', 'invisible_groups')

            new_optional.appendChild(new_attribute)
            rng_element.appendChild(new_optional)

    relaxng = etree.RelaxNG(
        etree.fromstring(rng_doc.toxml()))
    try:
        relaxng.assert_(doc)
    except Exception:
        _logger.info('The XML file does not fit the required schema !',
                     exc_info=True)
        _logger.info(misc.ustr(relaxng.error_log.last_error))
        raise

    if idref is None:
        idref = {}
    if isinstance(xmlfile, file):
        xml_filename = xmlfile.name
    else:
        xml_filename = xmlfile
    obj = xml_import(cr, module, idref, mode, report=report,
                     noupdate=noupdate, xml_filename=xml_filename)
    obj.parse(doc.getroot(), mode=mode)
    return True

convert.convert_xml_import = convert_xml_import
