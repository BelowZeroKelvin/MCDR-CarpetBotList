import re

bot_list = []


def on_info(server, info):
    if info.source == 0 and not info.is_player:
        botinfo = joined_info(info.content)
        if botinfo[0] and botinfo[1] == 'bot':
            server.say('§7假人[' + botinfo[2] + ']加入了游戏')
            bot_list.append(botinfo[2])
    elif info.is_player:
        cmd = info.content.split()
        if len(cmd) == 1 and cmd[0] == '!!botlist':
            server.say('§7[假人列表]' + ','.join(bot_list))
        # elif len(cmd)==2 and cmd[0]=='!!botlist' and cmd[1]=='clear':
        #     bot_list.clear()
        #     server.say('§7已清空假人列表')


def on_player_left(server, player):
    if player in bot_list:
        bot_list.remove(player)
        server.say('§7假人[' + player + ']离开了游戏')


def on_load(server, old_module):
    global bot_list
    bot_list = old_module.bot_list


def joined_info(msg):
    joined_player = re.match(
        r'(\w+)\[([0-9\.:]+|local)\] logged in with entity id', msg)
    if joined_player:
        if joined_player.group(2) == 'local':
            return [True, 'bot', joined_player.group(1)]
        else:
            return [True, 'player', joined_player.group(1)]
    return [False]
