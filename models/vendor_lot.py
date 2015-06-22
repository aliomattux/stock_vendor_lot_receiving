from openerp.osv import osv, fields
from datetime import datetime

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
	'license_plates': fields.one2many('stock.vendor.lot', 'receipt', string="License Plates"),
	'start_time': fields.datetime('Start Time'),
	'end_time': fields.datetime('End Time'),
	'purchase': fields.many2one('purchase.order', 'Purchase'),
	'vendor':fields.many2one('res.partner', 'Vendor'),
    }


    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.vendor.receipt') or '/'

	if not context.get('start_time'):
	    vals['start_time'] = datetime.utcnow()
	
        return super(StockVendorReceipt, self).create(cr, uid, vals, context)


    def print_license_plates(self, cr, uid, ids, context=None):
	return True

    def reconcile_purchase_order(self, cr, uid, ids, context=None):
	return True


class StockVendorLot(osv.osv):
    _name = 'stock.vendor.lot'
    _rec_name = 'license_plate'

    def _get_picking_in(self, cr, uid, context=None):
        obj_data = self.pool.get('ir.model.data')
        type_obj = self.pool.get('stock.picking.type')
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], context=context)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)], context=context)
            if not types:
                raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))

        return types[0]

    _columns = {
	'receipt': fields.many2one('stock.vendor.receipt', 'Vendor Receipt'),
	'license_plate': fields.char('License Plate'),
        'vendor':fields.many2one('res.partner', 'Vendor'),
	'state': fields.selection([('draft', 'Draft'),
			('checkin', 'Ready to Count'),
			('verification', 'Pending Verification'),
			('exception', 'Exception'),
			('putaway', 'Pending Putaway'),
			('done', 'Done')
	], 'State'),
	'picking_type_id': fields.many2one('stock.picking.type', 'Deliver To', help="This will determine picking type of incoming shipment"),
	'purchase': fields.many2one('purchase.order', 'Purchase'),
	'lot_items': fields.one2many('stock.vendor.lot.line', 'vendor_lot', string="Lot Items"),
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


class StockVendorLotItem(osv.osv):
    _name = 'stock.vendor.lot.line'
    _columns = {
	'name': fields.char('Name'),
	'vendor_lot': fields.many2one('stock.vendor.lot', 'Vendor Lot'),
	'product_qty': fields.float('Quantity'),
	'product': fields.many2one('product.product', 'Product'),
    }
