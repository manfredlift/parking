import math
from parking.backend.db.dbaccess import DbAccess
from parking.backend.user_server.wsserver import UserSessions
from parking.shared.rest_models import ParkingLot
from parking.shared.ws_models import ParkingRequestMessage


class Engine():
    def __init__(self, dba: DbAccess, user_sessions: UserSessions):
        self.dba = dba
        self.user_sessions = user_sessions

    async def handle_request_allocation(self, user_id: int, request: ParkingRequestMessage) -> ParkingLot:
        rejections = self.user_sessions.get_user(user_id).rejections
        lots = await self.dba.get_available_parking_lots(request.location, 100, rejections)

        # Just take the first lot for now...
        return lots[0] if lots else None

    async def commit_allocation(self, user_id: int, park_id: int) -> bool:
        # TODO: This could fail due to a full parking lot, but we can't tell...
        # If it does fail due to that, then we should look for other
        # allocations
        result = await self.dba.allocate_parking_lot(user_id, park_id)
        return result

    async def remove_allocation(self, user_id: int) -> None:
        # Ask the WS stuff to deallocate the user
        # Update the DB of allocations
        pass

    async def recalculate_allocations(self, park_id: int) -> None:
        # Deallocate users if parking spaces are taken
        # Calculate the allocated users and find the furthest away
        lot = await self.dba.get_parking_lot(park_id)
        user_sessions = self.user_sessions
        overflow = lot.num_allocated - lot.num_available

        def sort_func(elem):
            user_loc = user_sessions.get_user(elem['user_id']).location
            return math.hypot(lot.location.lat - user_loc.lat, lot.location.long - user_loc.long)

        if overflow:
            allocations = await self.dba.get_parking_lot_allocations(park_id)
            allocations.sort(key=sort_func, reverse=True)
            for alloc in allocations[:overflow]:
                print(alloc)
                self.remove_allocation(alloc['user_id'])
