from odoo import models, fields, api, _


class HubSpotContact(models.Model):
    _name = "durpro_hubspot_import.hubspot_contact"
    _inherit = "durpro_hubspot_import.hubspot_model"
    _description = 'Carries information imported from Hubspot Contacts'

    hubspot_model_name = "contacts"
    hubspot_id_field = "hs_object_id"

    hs_object_id = fields.Char(string="HS Object ID", compute="_extract_hs_fields", store=True)
    hs_additional_emails = fields.Char(string="HS Additional Emails", compute="_extract_hs_fields", store=True)
    hs_calculated_phone_number = fields.Char(string="HS Phone Number", compute="_extract_hs_fields", store=True)
    hs_calculated_mobile_number = fields.Char(string="HS Mobile Number", compute="_extract_hs_fields", store=True)
    hs_email_domain = fields.Char(string="HS Email Domain", compute="_extract_hs_fields", store=True)
    firstname = fields.Char(string="HS First Name", compute="_extract_hs_fields", store=True)
    lastname = fields.Char(string="HS Last Name", compute="_extract_hs_fields", store=True)
    email = fields.Char(string="HS Email", compute="_extract_hs_fields", store=True)
    mobilephone = fields.Char(string="HS Mobile Phone", compute="_extract_hs_fields", store=True)
    phone = fields.Char(string="HS Phone", compute="_extract_hs_fields", store=True)
    address = fields.Char(string="HS Address", compute="_extract_hs_fields", store=True)
    city = fields.Char(string="HS City", compute="_extract_hs_fields", store=True)
    state = fields.Char(string="HS State", compute="_extract_hs_fields", store=True)
    zip = fields.Char(string="HS Zip", compute="_extract_hs_fields", store=True)
    country = fields.Char(string="HS Country", compute="_extract_hs_fields", store=True)
    hs_language = fields.Char(string="HS Language", compute="_extract_hs_fields", store=True)
    company = fields.Char(string="HS Company", compute="_extract_hs_fields", store=True)

    odoo_contact = fields.Many2one('res.partner', string='Matching Odoo Contact', compute='_match_contact', store=True)

    @api.depends("firstname", "lastname", "email")
    def _match_contact(self):
        """
        Matches the HubSpot Contacts represented by this RecordSet to res.partner objects. First match is carried out by
        email. If emails bring up more than one match, they are filtered for first + last name match. If email matching
        fails, then a case insensitive name match is tried as a last resort.
        """
        names = [n[0] if n[0] else "" + " " + n[1] if n[1] else "" for n in
                 zip(self.mapped("firstname"), self.mapped("lastname"))]
        email_dict = {p.email: p for p in self.env['res.partner'].search([('email', 'in', self.mapped("email"))])}
        name_dict = {p.name: p for p in self.env['res.partner'].search([('name', 'in', names)])}

        for rec in self:
            partner = False
            full_name = (rec.firstname if rec.firstname else "") + " " + (rec.lastname if rec.lastname else "")
            if rec.email in email_dict:
                partner = email_dict[rec.email]
            if not partner:
                if full_name in name_dict:
                    partner = name_dict[full_name]
            rec.odoo_contact = partner
