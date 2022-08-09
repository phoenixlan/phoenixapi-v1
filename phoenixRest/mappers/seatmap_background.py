def map_seatmap_background_no_metadata(seatmap_background, request):
    return {
        'uuid': str(seatmap_background.uuid),
        'url': seatmap_background.get_url(request)
    }