from odoo import models, fields, api, _
import time


class HubSpotImportWizard(models.TransientModel):
    _name = "durpro_hubspot_import.hubspot_import_wizard"
    _description = 'Allows for the importation of HubSpot data into Odoo Helpdesk Tickets (and associations)'

    def action_get_hubspot_tickets(self):
        self.env['durpro_hubspot_import.hubspot_ticket'].import_all()

    def action_get_hubspot_contacts(self):
        self.env['durpro_hubspot_import.hubspot_contact'].import_all()

    def action_get_hubspot_companies(self):
        self.env['durpro_hubspot_import.hubspot_company'].import_all()

    def action_get_hubspot_pipelines(self):
        self.env['durpro_hubspot_import.hubspot_pipeline'].import_all()

    def action_get_hubspot_emails(self):
        self.env['durpro_hubspot_import.hubspot_email'].import_all()

    def action_get_hubspot_notes(self):
        self.env['durpro_hubspot_import.hubspot_note'].import_all()

    def action_get_hubspot_owners(self):
        self.env['durpro_hubspot_import.hubspot_owner'].import_all()

    def action_associate_tickets_with_contacts(self):
        self.env['durpro_hubspot_import.hubspot_ticket'].import_associated_contacts()

    def action_associate_tickets_with_companies(self):
        self.env['durpro_hubspot_import.hubspot_ticket'].import_associated_companies()

    def action_associate_tickets_with_emails(self):
        self.env['durpro_hubspot_import.hubspot_ticket'].import_associated_emails()

    def action_associate_tickets_with_notes(self):
        self.env['durpro_hubspot_import.hubspot_ticket'].import_associated_notes()

    def action_get_attachments(self):
        """Get attachments for any loaded HubSpotNotes and HubSpotEmails. There is no "get_all" method for files."""
        domain = [('hs_attachment_ids', '!=', False)]
        notes_count = self.env['durpro_hubspot_import.hubspot_note'].search_count(domain)
        emails_count = self.env['durpro_hubspot_import.hubspot_email'].search_count(domain)
        page_size = 100
        for offset in range(0, notes_count, page_size):
            notes = self.env['durpro_hubspot_import.hubspot_note'].search(domain, offset=offset, limit=page_size)
            for note in notes:
                for file_id in str.split(note.hs_attachment_ids):
                    f = self.env['durpro_hubspot_import.hubspot_attachment'].import_one(file_id)
                    raw = f.get_data()
                    filename = f.name or "" + f.extension or ""
                    self.env['ir.attachment'].create({
                        'name': filename,
                        'raw': raw,
                        'res_model': note._name,
                    })
        for offset in range(0, emails_count, page_size):
            emails = self.env['durpro_hubspot_import.hubspot_email'].search(domain, offset=offset, limit=page_size)
            for email in emails:
                for file_id in str.split(email.hs_attachment_ids):
                    f = self.env['durpro_hubspot_import.hubspot_attachment'].import_one(file_id)
                    raw = f.get_data()
                    filename = f.name or "" + f.extension or ""
                    self.env['ir.attachment'].create({
                        'name': filename,
                        'raw': raw,
                        'res_model': note._name,
                    })


    def action_create_odoo_tickets(self):
        page_size = 1000
        no_tickets = self.env['durpro_hubspot_import.hubspot_ticket'].search_count([])
        for offset in range(0, no_tickets, page_size):
            # Only work on tickets that have a configured pipeline and stage to which to transfer
            tickets = self.env['durpro_hubspot_import.hubspot_ticket'].search([], offset=offset,
                                                                              limit=page_size).filtered(lambda r: (
                (r.pipeline and r.pipeline.helpdesk_team_id and r.pipeline_stage and r.pipeline_stage.helpdesk_stage)))
            for ticket in tickets:
                # Create a ticket in the right pipeline
                try:
                    create_date = time.strptime(ticket.create_date, "%Y-%m-%dT%H:%M:%S[.%f]Z")
                except:
                    try:
                        create_date = time.strptime(ticket.create_date, "%Y-%m-%dT%H:%M:%SZ")
                    except:
                        create_date = False
                hd_ticket = self.env['helpdesk.ticket'].create({
                    'name': ticket.subject or ticket.content or "No Subject",
                    'description': ticket.content,
                    'create_date': create_date,
                    'team_id': ticket.pipeline.helpdesk_team_id.id,
                    'stage_id': ticket.pipeline_stage.helpdesk_stage.id,
                    'user_id': ticket.user_id.id if ticket.user_id else False,
                    'partner_id': ticket.associated_contacts[
                        0].odoo_contact.id if ticket.associated_contacts else False,
                    'hubspot_ticket_id': ticket.id,
                })

                # For each associated mail message
                # TODO: Clean this up with better code reuse, maybe in a mixin class or just a function
                for note in ticket.associated_notes:
                    # Start by creating the attachments, then we'll link them up appropriately later
                    # We let ir.attachment guess the mimetype since HubSpot's file type field is non-MIME
                    attachments = []
                    if note.hs_attachment_ids:
                        try:
                            create_date = time.strptime(note.create_date, "%Y-%m-%dT%H:%M:%S[.%f]Z")
                        except ValueError:
                            try:
                                create_date = time.strptime(note.create_date, "%Y-%m-%dT%H:%M:%SZ")
                            except ValueError:
                                create_date = False
                        for attachment in note.hs_attachment_ids:
                            ir_att = self.env['ir.attachment'].create({
                                'name': attachment.get_filename(),
                                'type': 'binary',
                                'public': False,
                                'raw': attachment.get_data(),
                                'create_date': attachment.created_at,
                            })
                            attachments.append(ir_att)
                        hd_ticket.message_post(body=note.hs_note_body,
                                               message_type='comment',
                                               author_id=note.owner.user_id.odoo_user or False,
                                               attachment_ids=[a.id for a in attachments],
                                               date=create_date,
                                               )

                for email in ticket.associated_emails:
                    attachments = []
                    if email.hs_attachment_ids:
                        try:
                            create_date = time.strptime(email.create_date, "%Y-%m-%dT%H:%M:%S[.%f]Z")
                        except ValueError:
                            try:
                                create_date = time.strptime(email.create_date, "%Y-%m-%dT%H:%M:%SZ")
                            except ValueError:
                                create_date = False
                        for attachment in note.hs_attachment_ids:
                            ir_att = self.env['ir.attachment'].create({
                                'name': attachment.get_filename(),
                                'type': 'binary',
                                'public': False,
                                'raw': attachment.get_data(),
                                'create_date': attachment.created_at,
                            })
                            attachments.append(ir_att)
                        hd_ticket.message_post(subject=email.hs_email_subject,
                                               body=email.hs_email_html or email.hs_email_text,
                                               message_type='email',
                                               author_id=email.author or False,
                                               email_from=email.hs_email_from_email if not email.author else False,
                                               partner_ids=email.recipients.ids,
                                               attachment_ids=[a.id for a in attachments],
                                               date=create_date,
                                               )
