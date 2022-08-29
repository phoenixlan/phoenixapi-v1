from phoenixRest.mappers.seatmap_background import map_seatmap_background_no_metadata
from phoenixRest.mappers.row import map_row_for_availability

def map_seatmap_for_availability(seatmap, request):
    return {
        'uuid': str(seatmap.uuid),
        'background_url': seatmap.background.get_url(request) if seatmap.background is not None else None,
        'rows': [ map_row_for_availability(row, request) for row in seatmap.rows ],
        'width': seatmap.width,
        'height': seatmap.height
    }