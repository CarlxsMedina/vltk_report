{
    'name': 'VLTK Custom Report Layout',
    'version': '1.0',
    'sequence': 999,  # Load LAST to avoid conflicts
    'depends': [
        'base',
        'web',
        'account',
        'tgr_l10n_sv_edi'
    ],
    'data': [
        'data/paperformat.xml',
        'data/report_actions.xml',
        'views/report_layout_custom.xml',
        'views/report_invoice_custom.xml',
        'views/layout_wizard_view.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}