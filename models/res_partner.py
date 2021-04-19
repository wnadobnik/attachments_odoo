from odoo import api, fields, models, exceptions
import os
import shutil
import re

CONTAINER_DIR = 'CAD'


class PartnerCatalogue(models.Model):
    _inherit = 'res.partner'

    catalogue = fields.Char(string='Katalog partnera')
    path_absolute = fields.Char(string='Ścieżka folderu klienta', compute="_compute_path_absolute")
    location = fields.Char(compute='_compute_location')

    folder_icon = fields.Html(compute="_compute_folder_icon")

    def change_cat_name(self):
        if self.catalogue and self.location:
            if os.path.isdir(CONTAINER_DIR + self.location + self.catalogue):
                catalogue_ref = self._get_catalogue()
                os.rename(CONTAINER_DIR + self.location + self.catalogue,
                            CONTAINER_DIR + self.location + catalogue_ref)
                self.write({'catalogue': catalogue_ref})
        else:
            self.craft()

    def change_type(self):
        if os.path.isdir(CONTAINER_DIR + self.location + self.catalogue):
            raise exceptions.Warning('Folder klienta o podanej nazwie już istnieje. Wybierz inną nazwę.')
        else:
            if self.is_company:
                start = '/indywidualne/'
            else:
                start = '/'
        os.rename(CONTAINER_DIR + start + self.catalogue, CONTAINER_DIR + self.location + self.catalogue)
        load = self.env['crm.lead'].search([('partner_id', '=', self.id)])
        for record in load:
            record.write({'path': start + self.catalogue})

    def change_has_parent(self):
        load = self.env['crm.lead'].search([('partner_id', '=', self.id)])
        if self.parent_id:
            for record in load:
                record.change_location()
            shutil.rmtree(CONTAINER_DIR + '/indywidualne/' + self.catalogue, ignore_errors=True)

    def craft(self):
        self.write({'catalogue': self._get_catalogue()})
        os.mkdir(CONTAINER_DIR + self.location + self.catalogue)

    @api.depends('is_company','parent_id')
    def _compute_location(self):
        for record in self:
            if record.is_company or record.parent_id:
                record.location = '/'
            else:
                record.location = '/indywidualne/'

    @api.depends('catalogue')
    def _compute_path_absolute(self):
        for record in self:
            if record.catalogue and record.location:
                record.path_absolute = 'odoo://Z:' + record.location
                if record.parent_id:
                    record.path_absolute += record.parent_id.catalogue
                else:
                    record.path_absolute += record.catalogue
            else:
                record.path_absolute ='brak folderu'

    def _get_catalogue(self):
        x = 0
        client_cat = self.name.split(' ')
        if len(client_cat) >= 2:
            client_cat = str(client_cat[0] + '_' + client_cat[1])
            client_cat = client_cat.upper()
        else:
            client_cat = str(client_cat[0])
            client_cat = client_cat.upper()

        while True:
            if x != 0:
                client_cat += '_' + str(x)
            location = CONTAINER_DIR + '/' + self.location + client_cat
            if not os.path.isdir(location):
                break
            x += 1
        return client_cat

    @api.depends('path_absolute')
    def _compute_folder_icon(self):
        for record in self:
            if record.catalogue:
                record.folder_icon = '<a href="' + record.path_absolute + '"><i class="fa fa-folder fa-2x" aria-hidden="false" role="img"/></a>'
            else:
                record.folder_icon = ''
