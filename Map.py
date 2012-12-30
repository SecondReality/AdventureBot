class Direction:
    NO_DIRECTION = -1
    NORTH = 0
    NORTHEAST = 1
    EAST = 2
    SOUTHEAST = 3
    SOUTH = 4
    SOUTHWEST = 5
    WEST = 6
    NORTHWEST = 7
    long_text = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    abbreviated_text = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]

    @staticmethod
    def direction_to_string(direction):
        # TODO: find the equivalent of an assert
        return Direction.long_text[direction]

class Room:
    def __init__(self):
        self.connections = {}
        self.id = 0

    def __repr__(self):
        return 'Room id ' + str(self.id) + ' connections ' + str(self.connections)

# Map handles the creation of the world map and the positioning of the player.
class Map:

#Input should be any data to associate with the room ( RoomData class ) and a map
    #maybe a map of data?
    # we don't even need to do that, we can handle stuff like that outside this class. but then where?
    def __init__(self):
        self.position = 0
        self.rooms = {}

        # Create the rooms:
        self.make_connection(0, 1, Direction.NORTH)
        self.make_connection(1, 2, Direction.NORTH)
        self.make_connection(2, 3, Direction.NORTHEAST)
        self.make_connection(2, 4, Direction.NORTHWEST)

    def get_connections(self, room_id):
        return self.rooms[room_id].connections

    def get_direction_from_string(self, text):
        if (text in Direction.long_text):
            return Direction.long_text.index(text)
        elif (text in Direction.abbreviated_text):
            return Direction.abbreviated_text.index(text)

        return Direction.NO_DIRECTION

    # Moves the player in the direction given. If the direction isn't available, returns false.
    def go_direction(self, direction): # int (Direction)
        room = self.get_room(self.position)
        if direction in room.connections:
            self.position = room.connections[direction]
            return True
        else:
            return False

    # private const function:
    def opposite_direction(self, direction):
        direction += 4
        direction %= 8
        return direction

    # Creates and returns a new room if the given id doesn't exist
    # Why not create all the rooms initially so I don't have to worry about this?
    def get_room(self, room_id):
        if room_id in self.rooms:
            return self.rooms[room_id]
        room = Room()
        room.id = room_id
        # Add the new room to the dictionary
        self.rooms[room_id] = room
        return room

    # Todo: check if connections already contain the room id (if so, it's an error)
    # Instead of using get_room it should just throw an error if the room doesn't exist.
    def make_connection(self, room_a_id, room_b_id, direction):
        room_a = self.get_room(room_a_id)
        room_a.connections[direction] = room_b_id

        room_b = self.get_room(room_b_id)
        room_b.connections[self.opposite_direction(direction)] = room_a_id