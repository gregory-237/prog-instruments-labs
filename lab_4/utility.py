from db_order import DatabaseOrder


def start_places(order_id) -> int:
    oldest_order = DatabaseOrder().select_info_order(order_id.split('_')[0] + '_1_' + order_id.split('_')[2])
    return oldest_order[4]


def has_places(order_id, number_places: int = 1) -> int:
    places_limit = start_places(order_id)
    sum_places = 0
    for i in range(1, 100):
        try:
            sum_places += DatabaseOrder().select_info_order(order_id.split('_')[0] + f'_{i}_' + order_id.split('_')[2])[2]
        except:
            return sum_places + number_places - 1 < int(places_limit)

