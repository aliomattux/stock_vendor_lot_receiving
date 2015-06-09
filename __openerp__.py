{
    'name': 'Stock Vendor Lot Receiving',
    'version': '1.1',
    'author': 'Kyle Waid',
    'category': 'Sales Management',
    'depends': ['purchase'],
    'website': 'https://www.gcotech.com',
    'description': """ 
    """,
    'data': ['views/vendor_lot.xml',
	'wizard/vendor_wizard_lot.xml',
	'wizard/lot_assign_vendor.xml',
	'data/vendor_lot_sequence.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
