from openerp.osv import osv, fields


class StockMove(osv.osv):
    _inherit = 'stock.move'
    _columns = {
	'stock.vendor.lot.line': fields.many2one('stock.vendor.lot.line', 'Vendor Receipt Line'),
    }


class StockPickingType(osv.osv):
    _inherit = 'stock.picking.type'

    def _get_vendor_lots_count(self, cr, uid, ids, field_names, arg, context=None):
        obj = self.pool.get('stock.vendor.lot')
        domains = self._get_vendor_lots_count_domains()
        result = {}
        for field in domains:
            data = obj.read_group(cr, uid, domains[field] +
                [('picking_type_id', 'in', ids)],
                ['picking_type_id'], ['picking_type_id'], context=context)
            count = dict(map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
            for tid in ids:
                result.setdefault(tid, {})[field] = count.get(tid, 0)
        return result


    _columns = {
        'count_incoming_new_lots': fields.function(_get_vendor_lots_count,
                type='integer', multi='_get_vendor_lots_count'),
        'count_incoming_ready_lots': fields.function(_get_vendor_lots_count,
                type='integer', multi='_get_vendor_lots_count'),
        'count_incoming_approval_lots': fields.function(_get_vendor_lots_count,
                type='integer', multi='_get_vendor_lots_count'),
        'count_incoming_exception_lots': fields.function(_get_vendor_lots_count,
                type='integer', multi='_get_vendor_lots_count'),
        'count_incoming_putaway_lots': fields.function(_get_vendor_lots_count,
                type='integer', multi='_get_vendor_lots_count'),
    }


    def _get_vendor_lots_count_domains(self, context=False):
        domains = {
            'count_incoming_new_lots': [('state', '=', 'draft')],
            'count_incoming_ready_lots': [('state', '=', 'checkin')],
            'count_incoming_approval_lots': [('state', '=', 'verification')],
            'count_incoming_exception_lots': [('state', '=', 'exception')],
            'count_incoming_putaway_lots': [('state', '=', 'putaway')],

        }

        return domains
