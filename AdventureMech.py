from errbot import BotPlugin, botcmd
import re
import xmpp
import logging
import threading
import random
from Map import Direction, Map

robot_name = 'Smashing Robot'

# Enemies to do:
# Tenga Toppa Gurren Laggan!
# Godzilla
# Metal Gear RAY
# Anubis

# Returns the first element of a list if it exists, otherwise None
def first(list):
    return list[0] if list else None


# An Action is a skill that has a certain amount of cooldown.
# Actions are stored in Player and in Mech
# Possibly rename to TimedAction?
class Action(object):
    def __init__(self, name, duration, repeat):
        self.name=name
        self.active=False
        self.duration=duration
        self.repeat=repeat
        self.last_activation_time=0

    # This is called when the action is first executed, use this for instant commands like attack.
    def on_activate(self, game):
        pass

    # This is used after a whole cycle - this should be used for commands that take a duration, like repair.
    def on_complete(self, game):
        pass

    def update(self, game):
        if not self.active:
            return

        difference = game.global_ticks - self.last_activation_time
        if difference >= self.duration:
            self.last_activation_time = game.global_ticks
            if not self.repeat:
                self.active=False
            self.on_activate(game)

class PlayerAttackAction(Action):
    def __init__(self, name, duration, player): # target = Entity
        super(PlayerAttackAction, self).__init__(name, duration, True)
        self.player = player
        self.target = None

    def on_activate(self, game):
        if not self.target:
            self.active=False
            return
        if game.attack_target(self.player, self.target):
            self.active=False

    def on_user_left_room(self, game):
        self.active = False

class PlayerRepairAction(Action):
    def __init__(self, name, duration, player): # target = Entity
        super(PlayerRepairAction, self).__init__(name, duration, False)
        self.player = player
        self.target = None

    def on_activate(self, game):
        # 'Name is starting to repair AdventureBot's head'
        if not self.target:
            self.active=False
            return
        if game.attack_target(self.player, self.target):
            self.active=False

        def on_complete(self, game):
            # Increase the robots level. Higher level people repair for more.
            # If bot is full health then disabling repair.

    def on_user_left_room(self, game):
        self.active = False

# Entity includes enemies and friendly NPCs (should the Mech be an entity?)
class Entity(object):
    def __init__(self, healthIn, nameIn, locationIn):
        self.health = healthIn
        self.name = nameIn
        self.location = locationIn

    # This is called 5 times a second for each active entity
    def update(self, game): # Takes the instance of AdventureMech so that it can modify the world.
        game.sendMessage('I am being updated')

    # Called when the user attacks this entity:
    # Return true if the entity should be removed.
    # (alternatively we could set a flag in the entity)
    def on_attacked(self, game):
        pass

    # Called when the user enters the room
    def on_user_entered_room(self, game):
        pass

    # Called when the user leaves the room
    def on_user_left_room(self, game):
        pass

def seconds_to_updates(seconds):
    return seconds * 10

# The simplest type of enemy.
# It's either passive or aggro and once it starts attacking it doesn't stop.
# It contains an array of different attacks.
class SimpleEnemy(Entity):
    def __init__(self, healthIn, nameIn, locationIn):
        super(SimpleEnemy, self).__init__(healthIn, nameIn, locationIn)
        self.on_attack_text =\
        [
            'The rat gnaws on '+robot_name+'\'s  toes.',
            'The rat scratches '+robot_name+'\'s leg.'
        ]
        self.on_death_strings = [
            'Congratulations! You\'re a 300 foot tall, multi-piloted war titan and you killed a rat.',
            'The rat explodes. A crater is left where the rat was standing.'
        ]
        self.on_enter_strings =\
        [
            'A rat is nibbling on something.'
        ]
        self.on_damage_strings =\
        [
            'The rat whimpers'
        ]
        self.detailed_look = 'A large brown rat with long whiskers.'
        self.on_player_kill = 'A laughing noise comes from the '+self.name+'.'

        self.attack_cooldown = 5 # The attack cool-down in seconds.
        self.attack_counter = 0
        self.is_attacking = False
        self.attack_power = 10
        self.xp = 1000

    # Called when the user attacks this entity:
    def on_attacked(self, game, power):
        self.health-=power
        if(self.health<=0):
            game.sendMessage(random.choice(self.on_death_strings))
            game.sendMessage('The '+self.name+' is dead. You gain '+str(self.xp)+'xp.')
            game.gain_xp(self.xp)
            return True
        else:
            game.sendMessage(random.choice(self.on_damage_strings)+' and loses '+str(power)+' health (' + str(self.health)+' remaining).')
        self.is_attacking = True

    # Called when the user enters the room:
    def on_user_entered_room(self, game):
        # Show the image of this enemy:
        urlname = self.name.replace('-', '').lower()
        game.sendMessage('<html><body><img src="http://secondreality.co.uk/adventurebot/'+urlname+'.jpg"/></body></html>')
        game.sendMessage(random.choice(self.on_enter_strings))

    # Called when the user leaves the room
    def on_user_left_room(self, game):
        pass

    def update(self, game):
        if(self.is_attacking):
            if game.map.position==self.location:
                self.attack_counter += 1

                if self.attack_counter >= seconds_to_updates(self.attack_cooldown):
                    self.attack_counter = 0
                    game.on_player_damaged(random.choice(self.on_attack_text), self.attack_power)
            else:
                # TODO: Decide if we want to follow the player here
                pass

class Player:
    ranks = ['noob', 'grunt', 'veteran', 'commander', 'master chief']

    def __init__(self, nameIn):
        self.name = nameIn
        self.level = 1
        self.xp = 0
        self.actions = []
        self.attack_action = PlayerAttackAction('attack', seconds_to_updates(3), self)

    def formal_identifier(self):
        return self.title()+' '+self.name

    def title(self):
        if self.level < len(Player.ranks):
            return Player.ranks[self.level]
        else:
            return 'big boss'

    def xp_required_for_level(self, level):
        return 100

    # If the player levels up, returns True
    def gain_xp(self, xpIn):
        current_xp_required_for_level = self.xp_required_for_level(self.level)
        self.xp+=xpIn
        if self.xp > current_xp_required_for_level:
            self.level+=1
            self.xp = 0
            return True
        return False

    def update(self, game):
        pass

    def on_user_left_room(self, game):
        self.attack_action.on_user_left_room(game)

class BodyPart:
    def __init__(self, nameIn):
        self.pilots = [] # An array of Players.
        self.health = 100
        self.name = nameIn

class Mech:
    LEGS = 0
    ARMS = 1
    HEAD = 2

    legs = BodyPart("legs")
    arms = BodyPart("arms")
    head = BodyPart("head")

    parts = [legs, arms, head]

    def __init__(self):
        self.health = 100

    def add_pilot(self, bodypart, player):
        if not player in self.parts[bodypart].pilots:
            self.parts[bodypart].pilots.append(player)

    # returns the least populous body part, giving preference to the feet
    def leastPopulousMechBodyPart(self):
        popularity = [] # (int[section]->)
        # Returns the index of the least populous mech section:

        popularity.append(len(self.legs.pilots))
        popularity.append(len(self.arms.pilots))
        popularity.append(len(self.head.pilots))

        # now find the index of the greatest value:
        return popularity.index(min(popularity))

class RoomData:
    def __init__(self, descriptionIn):
        self.description = descriptionIn

class AdventureMech(BotPlugin):
    GAMEROOM = '31171_gameroom@conf.hipchat.com'
    mech = Mech()
    map = Map()
    players = [] # [Player]

    roomData =\
    {
        0: RoomData('a small cave overlooking some fields.'),
        1: RoomData('a dusty path.'),
        2: RoomData('a grassy path. It branches into two paths. A sign pointing to the northeast reads "BEWARE".'),
        3: RoomData('a round clearing surrounded by trees.'),
        4: RoomData('a valley surrounded by large limestone cliffs.'),
        5: RoomData('a valley. The cliffs to either side of you don\'t leave much room to manoeuvre. You can see the path widens to the north west'),
        6: RoomData('large stones piled around a stone circle made of bricks.')
    }

    entities = []
    entities.append(SimpleEnemy(100, 'rat', 1))


    enemy_atat = SimpleEnemy(1000, 'AT-AT', 3)

    enemy_atat.on_attack_text =\
    [
        'The AT-AT fires two red lasers at '+robot_name+'.',
        'The AT-AT fires two head-mounted machine-guns at '+robot_name+'.'
    ]
    enemy_atat.on_death_strings = [
        'Congratulations! You\'re a 300 foot tall, multi-piloted war titan and you killed a rat.',
        'The rat explodes. A crater is left where the rat was standing.'
    ]
    enemy_atat.on_enter_strings =\
    [
        'A giant quadruped robot is walking in circles, and making a lot of noise.'
    ]
    enemy_atat.on_damage_strings =\
    [
        'Sparks shower from the AT-AT.'
    ]
    enemy_atat.detailed_look = 'A large white quadrupedal robot. It moves jerkily, almost as though it was filmed using stop motion.'
    entities.append(enemy_atat)

    active_entities = None

    def gain_xp(self, xp):
        for player in self.players:
            if player.gain_xp(xp):
                self.sendMessage(player.formal_identifier()+' is now level '+str(player.level)+'.')

    def direction_regex(self):
        direction_strings = Direction.long_text + Direction.abbreviated_text
        direction_strings.sort()
        direction_strings.reverse()
        return '('+'|'.join(direction_strings)+')'

    def __init__(self):
        # We update our world 10 times a second.
        self.global_ticks = 0
        self.start_poller(0.1, self.update)

        # Hook up our commands:
        self.commands = {}
        commands =\
        {
            "(?:go\s+)?"+self.direction_regex(): self.direction_command,
            "look(?:\s+(?:at\s+)?(\S+))?": self.lookCommand,
            "attack\s*(\S+)?$": self.attackCommand
        }

        for command in commands:
            pattern = re.compile(command)
            self.commands[pattern] = commands[command]

    # Should be done with filter or list comprehensions
    def get_entities_in_room(self, room_id):
        return filter(lambda x: x.location == room_id, self.entities)

    def update(self):
        self.global_ticks+=1

        #logging.debug('tick '+ threading.current_thread().name)
        for entity in self.entities:
            entity.update(self)

        for player in self.players:
            player.attack_action.update(self)

    def on_player_damaged(self, attack_text, power):
        self.mech.health-=power
        if self.mech.health<=0:
            self.sendMessage(attack_text + ' You lose ' + str(power)+' health. You have zero health.')
            self.sendMessage(attack_text + ' AdventureBot explodes. Bits of robot are all over the place.')
        else:
            self.sendMessage(attack_text + ' You lose ' + str(power)+' health ('+ str(self.mech.health)+' health remaining).')

    # Trims whitespace from a string and makes it lowercase
    def trimAndLowerCase(self, text):
        return text

    def add_player(self, playerName, player, bodypart): # string, Player, int
        self.sendMessage(player.formal_identifier()+' is now piloting AdventureMech\'s '+self.mech.parts[bodypart].name+'.')
        self.players.append(player)
        self.mech.add_pilot(bodypart, player)

    def get_player(self, playerName):
        filtered = filter(lambda x: x.name == playerName, self.players)
        return first(filtered)

    def sendMessage(self, message):
        jid = xmpp.protocol.JID(AdventureMech.GAMEROOM)
        self.send(jid, message, message_type='groupchat')

    # Given a list of strings it will join them with commas, properly ending it with 'and'
    # e.g.  ["cat", "dog", "bird"] -> "cat, dog and bird"
    # warning: modifies input array.
    def join_strings_with_commas_and_and(self, list):
        if len(list) > 1:
            last_item = list[-1]
            list.pop()
            result = ', '.join(list)
            result += ' and ' + last_item
            return result
        elif len(list)==1:
            return list[0]
        else:
            # TODO: assert
            pass

    def get_available_direction_text(self): # ()-> string
        # Get the exits of the room:
        directions = self.map.get_connections(self.map.position).keys()

        if len(directions) > 1:
            # TODO: use join_strings_with_commas_and_and above.
            last_direction = directions[-1]
            directions.pop()
            direction_text = "There are exits to the "
            direction_strings = map(Direction.direction_to_string, directions)
            direction_text += ', '.join(direction_strings)
            direction_text += ' and ' + Direction.direction_to_string(last_direction) + '.'
            return direction_text

        elif len(directions) == 1:
            return 'There is an exit to the ' + Direction.direction_to_string(directions[-1]) + '.'
        else:
            # TODO: Log error.
            pass

    def lookCommand(self, matches, player):
        # The command might be a description of the room or a command to look at an entity:
        target = matches.group(1)
        if target:
            # Check if the target exists in our room:
            entities_in_room=self.get_entities_in_room(self.map.position)
            entity_with_name = first(filter(lambda x: x.name.lower() == target, entities_in_room))
            self.sendMessage(entity_with_name.detailed_look)
        else:
            self.look_in_room()

    def look_in_room(self):
        if(self.map.position in self.roomData):
            self.sendMessage("You see " + self.roomData[self.map.position].description)
        else:
            self.sendMessage("You are now in room " + str(self.map.position))
        self.sendMessage(self.get_available_direction_text())

        entities_in_room=self.get_entities_in_room(self.map.position)
        if len(entities_in_room) > 0:
            entities_in_room_description = "There is a "
            entity_names = map(lambda x: x.name, entities_in_room)
            entities_in_room_description+=self.join_strings_with_commas_and_and(entity_names)
            entities_in_room_description+=' in the room.'
            self.sendMessage(entities_in_room_description)

    def attack_target(self, player, entity):
        self.sendMessage(player.formal_identifier()+' commands '+ robot_name + ' to stomp on the ' + entity.name+'.')
        if entity.on_attacked(self, 20):
            # We remove the entity from the list
            del self.entities[self.entities.index(entity)]
            return True
        return False

    def attackCommand(self, matches, player):
        if matches.group(1)==None:
            self.sendMessage("What should I attack?")
        else:
            target = matches.group(1)
            # Check if the target exists in our room:
            entities_in_room=self.get_entities_in_room(self.map.position)
            entity_with_name = first(filter(lambda x: x.name.lower() == target, entities_in_room))

            if entity_with_name:
                player.attack_action.target = entity_with_name
                player.attack_action.active = True
            else:
                self.sendMessage('There is no '+target+' in here, '+player.formal_identifier()+'.')

    def direction_command(self, matches, player): # Direction
        direction_text = matches.group(1)
        direction = self.map.get_direction_from_string(direction_text)

        if self.map.go_direction(direction):
            # Stop any current attacks we are making:
            for player in self.players:
                player.on_user_left_room(self)

            # Send a message saying we have moved, and display the description for the new area.
            # Send messages to any entities to let them know we have entered the area
            self.sendMessage("You go " + Direction.long_text[direction]+'.')
            self.lookCommand(None, player)
            # Update any entities:
            entities_in_room=self.get_entities_in_room(self.map.position)
            for entity in entities_in_room:
                entity.on_user_entered_room(self)
        else:
            # Send a message telling the users that we can't go in that direction.
            self.sendMessage("There is no exit in that direction.")

    def executePlayerCommand(self, text, player): # (string, Player)
        for pattern in self.commands:
            matchObject = pattern.match(text)
            if matchObject:
                self.commands[pattern](matchObject, player)

    def processUnsignedPlayer(self, input, playerName): # (string, string)
        # First check if the player is attempting to sign up:
        if input[0] == "join":
            # Create a new player:
            player = Player(playerName)
            # Assign a bodypart:
            bodypart = self.mech.leastPopulousMechBodyPart()
            self.add_player(playerName, player, bodypart)
            self.sendMessage('Welcome to the game, '+player.formal_identifier()+'!')
            #    '<html><body><b>Welcome</b> to the game, '+player.formal_identifier()+'!</body></html>')

    def callback_message(self, conn, mess):
        #logging.debug('response '+ threading.current_thread().name)
        text = mess.getBody().strip().lower()
        split_text = text.split()
        print('Input received was: ' + str(input))
        #print('The full message is '+str(mess))
        name = mess.getFrom().getResource()

        if(name == ''):
            return

        # Check if the player is in the database, if not tell them to join:

        # TO: 31171_gameroom@conf.hipchat.com/Steven Rose
        # From :31171_gameroom@conf.hipchat.com/Steven Rose

        player = self.get_player(name)
        if player:
            print 'executing player command ' + str(player)
            self.executePlayerCommand(text, player)
        else:
            print 'executing unsigned player command ' + str(player)
            self.processUnsignedPlayer(split_text, name)


            #print mess
            #if str(mess).find('cookie') != -1:
            #  self.send(mess.getFrom(), 'room id is ' + str(self.world.position) + ' connections are ' + str(self.world.rooms), message_type=mess.getType())
            #self.send(mess.getFrom(), 'http://pypi.python.org/python-3.png', message_type=mess.getType())
            #"What what somebody said cookie !?", message_type=mess.getType())

