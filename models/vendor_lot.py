from openerp.osv import osv, fields
from pprint import pprint as pp
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class ProductProduct(osv.osv):
    _inherit = 'product.product'

    def base_pending_receive_query(self, partner_id):
	query = "SELECT DISTINCT line.product_id FROM purchase_order_line line" \
	"\nJOIN purchase_order purchase ON (purchase.id = line.order_id)" \
	"\nJOIN product_product product ON (product.id = line.product_id)" \
	"\nJOIN product_template template ON (product.product_tmpl_id = template.id)" \
	"\nWHERE purchase.lp_state IN ('pending_partial', 'confirm')" \
	"\nAND purchase.partner_id = %s" % partner_id
	return query


    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('search_default_categ_id'):
            args.append((('categ_id', 'child_of', context['search_default_categ_id'])))

	if context.get('search_receipt_lines') and context.get('partner_id'):
	    if context.get('product'):
		return [context.get('product')]
	    supplier = context.get('partner_id')
	    query = self.base_pending_receive_query(supplier)
	    if context.get('purchases'):
		print 'PURCHASES', context.get('purchases')
		purchase_ids = context.get('purchases')[0][2]
		if len(purchase_ids) > 1:
		    query += "\nAND purchase.id IN %s" % str(tuple(purchase_ids))
		else:
		    query += "\nAND purchase.id = %s" % purchase_ids[0]
	    for arg in args:
		if arg[0] == 'default_code':
		    query += "\nAND product.default_code %s '%s' GROUP BY line.product_id, product.default_code" % (arg[1], arg[2])
		elif arg[0] == 'name':
		    query += "\nAND template.name %s '%s' GROUP BY line.product_id, template.name" % (arg[1], arg[2])
		else:
		    query += "\nGROUP BY line.product_id"
		query += "\nHAVING SUM(product_qty - COALESCE(qty_received, 0)) > 0"

		cr.execute(query)
		results = cr.fetchall()
		return [res[0] for res in results]
	    query += "\nGROUP BY line.product_id HAVING SUM(product_qty - COALESCE(qty_received, 0)) > 0"
	    cr.execute(query)
            results = cr.fetchall()
            return [res[0] for res in results]

	else:
            res = super(ProductProduct, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
	    return res


class StockVendorReceiptLine(osv.osv):
    _name = 'stock.vendor.receipt.line'

    def onchange_product(self, cr, uid, ids, product_id, vendor):
	if not product_id:
	    return {'value': {}}
	product = self.pool.get('product.product').browse(cr, uid, product_id)
	query = "SELECT SUM(line.product_qty - COALESCE(line.qty_received, 0))" \
		"\nFROM purchase_order_line line" \
		"\nJOIN purchase_order purchase ON (line.order_id = purchase.id)" \
		"\nWHERE line.product_id = %s AND purchase.lp_state IN ('pending_partial', 'confirm')" % product_id
	if vendor:
	    query += "\nAND purchase.partner_id = %s" % vendor
	query += "\nGROUP BY product_id"
	if vendor:
	    query += ", purchase.partner_id"
	cr.execute(query)
	results = cr.fetchall()
	qtys = [res[0] for res in results]
	if qtys:
	    return {'value': {'name': product.default_code, 'qty_po_pending': qtys[0]}}


    def _pending_receipt_count(self, cr, uid, ids, field_name, arg, context=None):
        if not ids:
            return {}
	basket = []
	for id in ids:
	    id = str(id)
	    val_string = "(" + id + ")"
	    basket.append(val_string)
	basket_string = ','.join(basket)

	query = "WITH products AS (VALUES %s)" \
		"\nSELECT column1 as id, sum(line.product_qty - COALESCE(line.qty_received, 0))" \
		"\nAS qty_po_pending FROM products" \
		"\nJOIN stock_vendor_receipt_line rec_line ON (products.column1 = rec_line.id)" \
		"\nLEFT OUTER JOIN purchase_order_line line ON (rec_line.product = line.product_id)" \
		"\nLEFT OUTER JOIN purchase_order purchase ON "\
		"(purchase.id = line.order_id AND purchase.lp_state IN ('pending_partial', 'confirm'))" \
		"\nGROUP BY products.column1" % basket_string

	cr.execute(query)
        res = dict(cr.fetchall())
        return res


    def _pending_dock_count(self, cr, uid, ids, field_name, arg, context=None):
	cr.execute("""SELECT line.id, SUM(lot_line.product_qty)
		FROM stock_vendor_receipt_line line
		JOIN stock_vendor_lot lot ON (lot.receipt = line.receipt)
		LEFT OUTER JOIN stock_vendor_lot_line lot_line
		ON (lot_line.vendor_lot = lot.id AND lot_line.product = line.product)
		WHERE line.id IN %s GROUP BY line.id""", (tuple(ids),))
        res = dict(cr.fetchall())
        return res

    _columns = {
        'name': fields.char('Name'),
	'receipt': fields.many2one('stock.vendor.receipt', 'Receipt'),
        'product_qty': fields.float('Quantity'),
	'qty_po_pending': fields.function(_pending_receipt_count,
		method=True, type="float", string="Qty On Order"
	),
	'qty_pending_exception': fields.float('Qty to Review'),
	'qty_pending_dock': fields.function(_pending_dock_count,
		method=True, type="float", string="Qty On Dock"
	),
	'receipt_qty': fields.float('Pack Slip Qty'),
        'product': fields.many2one('product.product', 'Product'),
    }


class StockVendorReceipt(osv.osv):
    _name = 'stock.vendor.receipt'

    def _number_lots(self, cr, uid, ids, field_name, arg, context=None):
        if not ids:
            return {}
        cr.execute("""SELECT r.id, COUNT(l.id) FROM stock_vendor_receipt r
                LEFT OUTER JOIN stock_vendor_lot l ON (r.id = l.receipt)
                WHERE r.id IN %s GROUP BY r.id""", (tuple(ids),))

	res = dict(cr.fetchall())

	return res


    def action_view_license_plates(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, \
		'stock_vendor_lot_receiving', 'action_vendor_lot_form'
	)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]

        #compute the number of delivery orders to display
        plate_ids = []
        for receipt in self.browse(cr, uid, ids, context=context):
            plate_ids += [plate.id for plate in receipt.license_plates]
            
        #choose the view_mode accordingly
        result['domain'] = "[('id','in',[" + ','.join(map(str, plate_ids)) + "])]"

        return result


    def _get_lot_states_count_domains(self, context=False):
        domains = {
            'count_incoming_new_lots': [('state', '=', 'draft')],
            'count_incoming_ready_lots': [('state', '=', 'checkin')],
            'count_incoming_approval_lots': [('state', '=', 'verification')],
            'count_incoming_exception_lots': [('state', '=', 'exception')],
            'count_incoming_putaway_lots': [('state', '=', 'putaway')],

        }

        return domains


    def _get_lot_states_count(self, cr, uid, ids, field_names, arg, context=None):
        obj = self.pool.get('stock.vendor.lot')
        domains = self._get_lot_states_count_domains()
        result = {}
        for field in domains:
            data = obj.read_group(cr, uid, domains[field] +
                [('receipt', 'in', ids)],
                ['receipt'], ['receipt'], context=context)
            count = dict(map(lambda x: (x['receipt'] and x['receipt'][0], x['receipt_count']), data))
            for tid in ids:
                result.setdefault(tid, {})[field] = count.get(tid, 0)
        return result


    _columns = {
	'name': fields.char('Receipt'),
	'items': fields.one2many('stock.vendor.receipt.line', 'receipt', \
		string="Items", ondelete="cascade"
	),
	'number_lots': fields.function(_number_lots, method=True, type="integer", string="# Lots"),
        'count_incoming_new_lots': fields.function(_get_lot_states_count,
                type='integer', multi='_get_lot_states_count', string="New"),
        'count_incoming_ready_lots': fields.function(_get_lot_states_count,
                type='integer', multi='_get_lot_states_count', string="Ready to Count"),
        'count_incoming_approval_lots': fields.function(_get_lot_states_count,
                type='integer', multi='_get_lot_states_count', string="Pending Approval"),
        'count_incoming_exception_lots': fields.function(_get_lot_states_count,
                type='integer', multi='_get_lot_states_count', string="Exception"),
        'count_incoming_putaway_lots': fields.function(_get_lot_states_count,
                type='integer', multi='_get_lot_states_count', string="Pending Putaway"),
	'state': fields.selection([('cancel', 'Canceled'),
		('not_reconcile', 'Not Reconciled'),
		('discrepant', 'Discrepancy'),
		('reconcile', 'Reconciled')
	], 'State'),
	'license_plates': fields.one2many('stock.vendor.lot', 'receipt', string="License Plates"),
	'start_time': fields.datetime('Start Time'),
	'end_time': fields.datetime('End Time'),
	'vendor':fields.many2one('res.partner', 'Vendor', domain="[('supplier', '=', True)]"),
        'purchases': fields.many2many('purchase.order', \
                'stock_vendor_receipt_purchase_rel', 'receipt_id', 'purchase_id', \
                'Purchase Orders', domain="[('partner_id', '=', vendor)]"
        )
    }

    _defaults = {
	'state': 'not_reconcile',
    }

    def reconcile_lines_check(self, cr, uid, receipt, context=None):
	"""
	    Three step process
	    1. Get the lots involved in the reconcile to avoid a join
	    2. Select the sum quantity greater than 0 where there is a discrepancy
	    3. Update the receipt line with the correct quantities
	"""
	cr.execute("SELECT id FROM stock_vendor_lot WHERE receipt = %s"%receipt.id)
	lot_data = cr.fetchall()
	lots = [l[0] for l in lot_data]

	if not lots:
	    #TODO
	    _logger.info('There were no lots found to reconcile')
	    return True

	if len(lots) > 1:
	    operator = 'IN'
	    values = tuple(lots)
	else:
	    operator = '='
	    values = lots[0]

        query = "SELECT line.id, SUM(line.receipt_qty - COALESCE(lot_line.product_qty, 0)) " \
		"AS product_qty" \
                "\nFROM stock_vendor_receipt_line line" \
		"\nLEFT OUTER JOIN stock_vendor_lot_line lot_line " \
		"ON (lot_line.vendor_lot %s %s AND lot_line.product = line.product)" \
                "\nWHERE line.receipt = %s GROUP BY line.id" \
		"\nHAVING SUM(line.receipt_qty - COALESCE(lot_line.product_qty, 0)) > 0" % \
		(operator, values, receipt.id)

	cr.execute(query)
	results = cr.dictfetchall()
	if not results:
            query = "SELECT line.id, SUM(line.receipt_qty - COALESCE(lot_line.product_qty, 0)) " \
                "AS product_qty" \
                "\nFROM stock_vendor_receipt_line line" \
                "\nLEFT OUTER JOIN stock_vendor_lot_line lot_line " \
                "ON (lot_line.vendor_lot %s %s AND lot_line.product = line.product)" \
                "\nWHERE line.receipt = %s GROUP BY line.id" \
                "\nHAVING SUM(line.receipt_qty - COALESCE(lot_line.product_qty, 0)) < 0" % \
                (operator, values, receipt.id)

            cr.execute(query)
            results = cr.dictfetchall()
	if results:
	    update_query = "WITH sums AS (SELECT line.id AS line_id, " \
		"SUM(COALESCE(lot_line.product_qty, 0)) AS product_qty" \
		"\nFROM stock_vendor_receipt_line line" \
		"\nLEFT OUTER JOIN stock_vendor_lot_line lot_line ON " \
		"(lot_line.vendor_lot %s %s AND lot_line.product = line.product)" \
		"\nWHERE line.receipt = %s GROUP BY line.id)" \
		"\nSELECT line.id, SUM(line.receipt_qty - sums.product_qty) AS product_qty" \
		"\nFROM sums" \
		"\nJOIN stock_vendor_receipt_line line ON (sums.line_id = line.id)" \
		"\nGROUP BY line.id" % (operator, values, receipt.id)

	    cr.execute(update_query)
	    results = cr.dictfetchall()
	    cr.execute("UPDATE stock_vendor_lot SET state = 'exception' WHERE id IN %s", (tuple(lots),))

	    return results

	else:
	    cr.execute("UPDATE stock_vendor_lot SET state = 'putaway' WHERE id IN %s", \
		(tuple(lots),))
	    return False


    def reconcile_receipt(self, cr, uid, ids, context=None):
	receipt = self.browse(cr, uid, ids[0])
	line_obj = self.pool.get('stock.vendor.receipt.line')
	exception_lines = self.reconcile_lines_check(cr, uid, receipt)
	if not exception_lines:
	    _logger.info('All lines reconciled successfully')
	    cr.execute("UPDATE stock_vendor_receipt_line SET qty_pending_exception = 0 WHERE receipt = %s"%receipt.id) 
	    receipt.state = 'reconcile'
	    return

	_logger.info('The Reconcile did not pass')
	receipt.state = 'discrepant'
	for ex in exception_lines:
	    line_obj.write(cr, uid, ex['id'], {'qty_pending_exception': ex['product_qty']})
	return True	


    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.vendor.receipt') or '/'

	if not context.get('start_time'):
	    vals['start_time'] = datetime.utcnow()
	
        return super(StockVendorReceipt, self).create(cr, uid, vals, context)


    def print_license_plates(self, cr, uid, ids, context=None):
	return True


class StockVendorLot(osv.osv):
    _name = 'stock.vendor.lot'
    _rec_name = 'license_plate'

    def _get_picking_in(self, cr, uid, context=None):
        obj_data = self.pool.get('ir.model.data')
        type_obj = self.pool.get('stock.picking.type')
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        types = type_obj.search(cr, uid, [('code', '=', 'incoming'), \
		('warehouse_id.company_id', '=', company_id)], context=context
	)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), \
		('warehouse_id', '=', False)], context=context
	    )
            if not types:
                raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))

        return types[0]

    _columns = {
	'receipt': fields.many2one('stock.vendor.receipt', 'Vendor Receipt'),
	'license_plate': fields.char('License Plate'),
        'product_reference': fields.related('lot_items', 'product', type='many2one', \
                relation='product.product', string="Product Search"),
        'vendor':fields.many2one('res.partner', 'Vendor', domain="[('supplier', '=', True)]"),
	'location': fields.many2one('stock.location', 'Receiving Bin'),
	'state': fields.selection([('draft', 'Draft'),
			('checkin', 'Ready to Count'),
			('verification', 'Pending Verification'),
			('exception', 'Exception'),
			('putaway', 'Pending Putaway'),
			('done', 'Done')
	], 'State'),
	'picking_type_id': fields.many2one('stock.picking.type', 'Deliver To', \
		help="This will determine picking type of incoming shipment"
	),
        'purchases': fields.many2many('purchase.order', \
                'vendor_lot_purchase_rel', 'lot_id', 'purchase_id', \
		'Purchase Orders', domain="[('partner_id', '=', vendor)]"
        ),
	'lot_items': fields.one2many('stock.vendor.lot.line', 'vendor_lot', \
		string="Lot Items", ondelete="cascade"
	),
    }

    _defaults = {
	'state': 'draft',
	'picking_type_id': _get_picking_in
    }


    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if ('license_plate' not in vals) or (vals.get('license_plate') in ('/', False)):
	    vals['license_plate'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.vendor.lot') or '/'

        return super(StockVendorLot, self).create(cr, uid, vals, context)


    def confirm_vendor_lot(self, cr, uid, ids, context=None):
	return self.write(cr, uid, ids, {'state': 'verification'})


class StockVendorLotLine(osv.osv):
    _name = 'stock.vendor.lot.line'
    _columns = {
	'name': fields.char('Name'),
	'vendor_lot': fields.many2one('stock.vendor.lot', 'Vendor Lot'),
	'product_qty': fields.float('Quantity'),
	'product': fields.many2one('product.product', 'Product'),
	'location': fields.many2one('stock.location', 'Receiving Bin'),
    }
