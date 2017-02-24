{
    'name': 'Stock Vendor Lot Receiving',
    'version': '1.1',
    'author': 'Kyle Waid',
    'category': 'Sales Management',
    'depends': ['stock', 'purchase', 'pick_pack_ship'],
    'website': 'https://www.gcotech.com',
    'description': """ 
    """,
    'data': ['views/vendor_lot.xml',
	    'views/stock.xml',
	    'views/vendor_receipt.xml',
#	'wizard/vendor_wizard_lot.xml',
#	'wizard/mass_update_lots_from_lots.xml',
#	'wizard/mass_update_lots_from_receipt.xml',
#	'wizard/mass_create_lots.xml',
#	'wizard/add_items.xml',
	'data/vendor_lot_sequence.xml',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
