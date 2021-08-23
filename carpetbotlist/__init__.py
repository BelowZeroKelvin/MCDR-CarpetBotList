import re
from mcdreforged.api.types import PluginServerInterface, Info, CommandSource
from mcdreforged.api.rtext import RTextList, RText, RAction, RColor
from mcdreforged.api.command import Literal
from mcdreforged.api.decorator import new_thread

bot_list = []
player_list = []


worlds = {
    "minecraft:overworld": "§a主世界",
    "minecraft:the_end": "§d末地",
    "minecraft:the_nether": "§4地狱",
}


def joined_info(msg):
    joined_player = re.match(
        r"(\w+)\[([0-9\.\:\/]+|local)\] logged in with entity id", msg
    )
    if joined_player:
        if joined_player.group(2) == "local":
            return (True, "bot", joined_player.group(1))
        else:
            return (True, "player", joined_player.group(1))
    return (False,)


def get_player_pos(server, player):
    minecraft_data_api = server.get_plugin_instance("minecraft_data_api")
    dimension = minecraft_data_api.get_player_info(player, "Dimension")
    pos = minecraft_data_api.get_player_info(player, "Pos")
    return {
        "player": player,
        "dimension": dimension,
        "x": int(pos[0]),
        "y": int(pos[1]),
        "z": int(pos[2]),
    }


def list_bot(server: PluginServerInterface):
    new_list = []
    for bot in bot_list:
        new_list.append(get_player_pos(server, bot))
    return new_list


def msg_list_bot(server: PluginServerInterface):
    if not len(bot_list):
        return "§7服务器还没有假人"
    new_list = list_bot(server)
    msg = RTextList(RText("[假人列表]", color=RColor.gray))
    for bot in new_list:
        msg.append(
            RText("\n[x] ", color=RColor.red)
            .h("下线该假人")
            .c(RAction.run_command, f'/player {bot["player"]} kill'),
            RText(bot["player"]).h(
                RText(
                    f'[{worlds[bot["dimension"]]}§r] \n({bot["x"]},{bot["y"]},{bot["z"]}) '
                )
            ),
        )
    return msg


@new_thread("send_bot_list")
def send_bot_list(src: CommandSource):
    src.reply(msg_list_bot(src.get_server()))


def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    botinfo = joined_info(info.content)
    if botinfo[0]:
        if botinfo[1] == "bot":
            server.say("§7假人[" + botinfo[2] + "]加入了游戏")
            bot_list.append(botinfo[2])
        elif botinfo[1] == "player":
            player_list.append(botinfo[2])


def on_player_left(server: PluginServerInterface, player):
    if player in bot_list and player in player_list:
        player_list.remove(player)
    elif player in player_list:
        player_list.remove(player)
    elif player in bot_list:
        bot_list.remove(player)
        server.say("§7假人[" + player + "]离开了游戏")


def on_load(server: PluginServerInterface, old_module):
    global bot_list, player_list
    server.register_command(Literal("!!botlist").runs(lambda src: send_bot_list(src)))
    if old_module is not None:
        bot_list = old_module.bot_list
        player_list = old_module.player_list


def on_server_startup(server):
    global bot_list, player_list
    bot_list = []
    player_list = []
