{
    "name": "Durpro HubSpot Import",
    "version": "1.0",
    "license": "Other proprietary",
    "author": "Durpro Ltd",
    "category": "Generic Modules/Others",
    "depends": [
        "helpdesk",
    ],
    "external_dependencies": {"python": ["hubspot-api-client", "PIL",]},
    "description": """
    This module allows for importing records from HubSpot into Odoo.
    """,
    "demo": [],
    'data': [
        "data/hubspot_import_data.xml",
        "views/res_config_settings_views.xml",
        "views/hubspot_import_views.xml",
        "views/pipeline_views.xml",
        "security/ir.model.access.csv",
        "wizard/hubspot_import_wizard_views.xml",
    ],
    'test': [],
    'installable': True,
    'active': False
}
