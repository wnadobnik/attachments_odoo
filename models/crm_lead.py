from odoo import api, fields, models, exceptions
import os
import datetime
import base64
import shutil

CONTAINER_DIR = 'CAD'


class Lead_files(models.Model):
    _inherit = 'crm.lead'
    _order = 'is_mine desc, id desc'

    partner_id = fields.Many2one('res.partner')

    catalogue = fields.Char(string='Katalog nadrzędny', store=True, related='partner_id.catalogue')
    catalogue_lead = fields.Char(string='Katalog zlecenia')
    path = fields.Char(string='Katalog zlecenia')
    path_absolute = fields.Char(string="Link z przeglądarki", compute='_compute_path_absolute', store=False)
    location = fields.Char(compute='_compute_location')

    is_mine = fields.Integer(string='Moje?', compute='_compute_is_mine', store=False)

    last_offer = fields.Html(string="Link z przeglądarki", compute='_compute_last_offer')
    folder_icon = fields.Html(string='F', compute="_compute_folder_icon", store=False)

    folder_updated = fields.Datetime(string='Test pomiaru czasu')

    is_trash = fields.Boolean(string="W śmietniku")

    def build_file_structure(self):
        self.write({'catalogue_lead': self.get_cat_name(), 'path': self.location,
                    'folder_updated': fields.Datetime.now()})
        destination = CONTAINER_DIR + '/' + self.path + self.catalogue_lead
        if not os.path.isdir(CONTAINER_DIR + '/' + 'inne'):
            os.mkdir(CONTAINER_DIR + '/' + 'inne')
        if not os.path.isdir(CONTAINER_DIR + '/' + 'indywidualne'):
            os.mkdir(CONTAINER_DIR + '/' + 'indywidualne')
        if not os.path.isdir(destination):
            os.mkdir(destination)
            os.mkdir(destination + '/rozw')
            os.mkdir(destination + '/rys')
            os.mkdir(destination + '/job')

    def copy_files(self):
        destination = CONTAINER_DIR + '/' + self.path + self.catalogue_lead
        load = self.env['ir.attachment'].search([('res_model', '=', 'crm.lead'), ('res_id', '=', self.id)])
        for attachment in load:
            file = destination + '/' + attachment.name
            bin_value = base64.b64decode(attachment.datas)
            fp = open(file, 'wb')
            fp.write(bin_value)

    def update_files(self):
        if self.folder_updated:
            load = self.env['ir.attachment'].search(
                [('res_model', '=', 'crm.lead'), ('res_id', '=', self.id), ('create_date', '>', self.folder_updated)])
            destination = CONTAINER_DIR + '/' + self.location + self.catalogue_lead
            for attachment in load:
                if attachment.create_uid.name == "OdooBot":
                    file = destination + '/' + attachment.name
                    if os.path.isfile(file):
                        x = attachment.name.find(".", len(attachment.name) - 4, len(attachment.name))
                        i = 1
                        while True:
                            file = destination + '/' + attachment.name[0:x] + "(" + str(i) + ")" + attachment.name[
                                                                                                   x:len(
                                                                                                       attachment.name)]
                            if not os.path.isfile(file):
                                break
                                i += 1
                    bin_value = base64.b64decode(attachment.datas)
                    fp = open(file, 'wb')
                    fp.write(bin_value)
            self.write({'folder_updated': fields.Datetime.now()})

    def change_name(self):
        new_name = self.get_cat_name()
        os.rename(CONTAINER_DIR + '/' + self.path + self.catalogue_lead,
                  CONTAINER_DIR + '/' + self.path + new_name)
        self.write({'catalogue_lead': new_name})

    def change_location(self):
        location = CONTAINER_DIR + '/' + self.path + self.catalogue_lead
        destination = CONTAINER_DIR + '/' + self.location + self.catalogue_lead
        if os.path.isdir(location):
            os.rename(location, destination)
            self.write({'path': self.location})

    def get_cat_name(self):
        x = 0
        while True:
            job_cat = str(datetime.datetime.now().strftime('%y-%m-%d')) + '(' + self.name.replace(' ', '_')
            if x != 0:
                job_cat += '_' + str(x)
            job_cat += ')'
            location = CONTAINER_DIR + '/' + self.location + job_cat
            if not os.path.isdir(location):
                break
            x +=1
        return job_cat

    #computed fields

    @api.depends('partner_id','partner_id.is_company','partner_id.parent_id')
    def _compute_location(self):
        for record in self:
            if record.partner_id:
                if record.partner_id.is_company:
                    record.location = str(record.partner_id.catalogue) + '/'
                else:
                    if record.partner_id.parent_id:
                        record.location = str(record.partner_id.parent_id.catalogue) + '/'
                    else:
                        record.location = 'indywidualne/' + str(record.partner_id.catalogue) + '/'
            else:
                record.location = 'inne/'

    @api.depends('catalogue_lead')
    def _compute_path_absolute(self):
        for record in self:
                record.path_absolute = 'odoo://Z:/' + record.location + record.catalogue_lead


    @api.depends('user_id')
    def _compute_is_mine(self):
        for record in self:
            if record.user_id == record.env.user:
                record.is_mine = 1
            else:
                record.is_mine = 0

    def _compute_last_offer(self):
        for record in self:
            offer = self.env['sale.order'].search([('opportunity_id', '=', record.id)], order='id desc', limit=1)
            if offer:
                lines = self.env['sale.order.line'].search([('order_id', '=', offer[0].id)])
                result = '<table><tr><td width="200px"><b>Nazwa produktu/usługi</b></td><td width=100px"><b>Cena bez VAT</b></td></tr>'
                for line in lines:
                    result += '<tr><td>' + line.name + '</td><td>' + str(line.price_subtotal) + '<td></td>'
                result += '</table>'
                record.last_offer = result
            else:
                record.last_offer = "Nie ma :("

    def _compute_folder_icon(self):
        for record in self:
            if record.catalogue_lead and record.path:
                record.folder_icon = '<a href="' + record.path_absolute + \
                                     '"><i class="fa fa-folder" aria-hidden="false" role="img"/></a>'
            else:
                record.folder_icon = False

    #override unlink function to delete physical

    def unlink(self):
        for record in self:
            if record.is_trash:
                if os.path.isdir(CONTAINER_DIR + '/' + record.path + record.catalogue_lead):
                    shutil.rmtree(CONTAINER_DIR + '/' + record.path + record.catalogue_lead, ignore_errors=True)
                    return super(Lead_files, record).unlink()
            else:
                raise exceptions.Warning('Zlecenie ' + record.name  + ' nie znajduje się w śmietniku i nie można go usunąć!')

    def trash(self):
        for record in self:
            if record.is_trash:
                record.write({'is_trash': False})
            else:
                record.write({'is_trash': True})

    def paint(self):
        if self.user_id.user_color_id:
            self.write({'color': int(self.user_id.user_color_id)})
