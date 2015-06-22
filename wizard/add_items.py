from openerp.osv import osv, fields
from openerp.tools.translate import _

class StockVendorLotItemWizard(osv.osv):
    _name = 'stock.vendor.lot.item.wizard'
    _columns = {
	'hidden_vendor_lot': fields.many2one('stock.vendor.lot', 'License Plate'),
	'items_count': fields.integer('Items Added'),
	'product_id': fields.integer('Product ID'),
	'hidden_product_id': fields.integer('Product ID'),
	'vendor_lot': fields.many2one('stock.vendor.lot', 'License Plate'),
	'product': fields.many2one('product.product', 'Product'),
	'items': fields.one2many('stock.vendor.lot.items.wizard', 'parent', string='Vendor Lots'),
	'sku': fields.char('Sku'),
	'product_qty': fields.float('Quantity to Add'),
	'length': fields.float('Length'),
	'width': fields.float('Width'),
	'height': fields.float('Height'),
	'weight': fields.float('Weight'),
	'upc': fields.char('UPC'),
	'product_name': fields.char('Product Name'),
    }


    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
	#There is some bug where the wizard default get is called multiple times
	#context is immutable so we will check if this is the only field then we
	#know its a bogus call and immediately return
	if fields == ['vendor_lot']:
	    return {}

	vendor_lot_id = context.get('active_id')
	lot_obj = self.pool.get('stock.vendor.lot')
	lot = lot_obj.browse(cr, uid, vendor_lot_id)
	items = []
	res = {
		'hidden_vendor_lot': vendor_lot_id,
		'vendor_lot': vendor_lot_id,
	}	

	if context.get('default_items'):
	    items = context.get('default_items')
	    res['items'] = items
	    res['items_count'] = context.get('default_items_count')

	else:
	    for item in lot.lot_items:
	        items.append({'existing_lot_item': item.id,
			      'product_qty': item.product_qty,
			      'product': item.product.id,
	        })
	    res['items_count'] = len(items)

	    res['items'] = items


	return res


    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
	if not product_id:
	    return {'value': {
			'product_id': False,
			'hidden_product_id': '',
			'sku': '',
			'product_name': '',
			'upc': '',
			'length': '',
			'width': '',
			'height': '',
	    }}

	product = self.pool.get('product.product').browse(cr, uid, product_id)
	vals = {
		'product_id': product.id,
		'hidden_product_id': product.id,
		'sku': product.default_code,
		'product_name': product.name,
		'upc': product.upc,
		'length': product.length,
		'width': product.width,
		'height': product.height,
#		'weight':
	}

	return {'value': vals}


    def prepare_product_vals(self, cr, uid, wizard, context=None):
	vals = {
		'name': wizard.product_name,
		'upc': wizard.upc,
		'default_code': wizard.sku,
		'length': wizard.length,
		'width': wizard.width,
		'height': wizard.height,
	}

	return vals


    def save_progress(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	lot_id = wizard.hidden_vendor_lot.id
	line_obj = self.pool.get('stock.vendor.lot.line')

        query = "SELECT product, product_qty" \
                "\nFROM stock_vendor_lot_items_wizard" \
                "\nWHERE parent = %s AND existing_lot_item IS NULL" % wizard.id

        cr.execute(query)

        items = cr.dictfetchall()
	print 'ITEMS', items
	if not items:
	    return True

	for item in items:
	    item['vendor_lot'] = lot_id
	    line_obj.create(cr, uid, item)

	return True


    def check_product_qty(self, wizard):
        if wizard.product_qty < 1:
	    raise osv.except_osv(_('User Error!'), _("You must add a quantity greater than 0"))

	return True


    def add_existing_item_and_continue(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	self.check_product_qty(wizard)
	line_obj = self.pool.get('stock.vendor.lot.items.wizard')
	product = wizard.hidden_product_id
	items = wizard.items
	vals = {'parent': wizard.id, 'product': product, 'product_qty': wizard.product_qty}
	line_obj.create(cr, uid, vals)

	return self.reload_wizard(cr, uid, wizard, context)


    def create_new_item_and_continue(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	self.check_product_qty(wizard)
	line_obj = self.pool.get('stock.vendor.lot.items.wizard')
	product_obj = self.pool.get('product.product')
	product_vals = self.prepare_product_vals(cr, uid, wizard)
	product_id = product_obj.create(cr, uid, product_vals)
	items = wizard.items
        vals = {'parent': wizard.id, 'product': product_id, 'product_qty': wizard.product_qty}
        line_obj.create(cr, uid, vals)

	return self.reload_wizard(cr, uid, wizard, context)


    def update_existing_item_and_continue(self, cr, uid, ids, context=None):
	wizard = self.browse(cr, uid, ids[0])
	self.check_product_qty(wizard)
	line_obj = self.pool.get('stock.vendor.lot.items.wizard')
	items = wizard.items
	product_obj = self.pool.get('product.product')
	product_vals = self.prepare_product_vals(cr, uid, wizard)
	product_id = wizard.hidden_product_id
	product_obj.write(cr, uid, product_id, product_vals)
        vals = {'parent': wizard.id, 'product': product_id, 'product_qty': wizard.product_qty}
        line_obj.create(cr, uid, vals)

	return self.reload_wizard(cr, uid, wizard, context)


    def reload_wizard(self, cr, uid, wizard, context):
	query = "SELECT product, product_qty, existing_lot_item" \
		"\nFROM stock_vendor_lot_items_wizard" \
		"\nWHERE parent = %s" % wizard.id

	cr.execute(query)

	items = cr.dictfetchall()

        context.update({
                'default_items_count': len(wizard.items),
		'default_items': items,
        })

        return {
            'name':_("Create License Plate"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'stock.vendor.lot.item.wizard',
            'type': 'ir.actions.act_window',
#            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }


class StockVendorLotItemsWizard(osv.osv):
    _name = 'stock.vendor.lot.items.wizard'
    _columns = {
	'existing_lot_item': fields.many2one('stock.vendor.lot.line', 'Existing Line'),
        'parent': fields.many2one('stock.vendor.lot.item.wizard', 'Parent'),
        'product': fields.many2one('product.product', string="Product"),
	'product_qty': fields.float('Product Qty'),
    }
