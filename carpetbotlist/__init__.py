import re
from typing import TYPE_CHECKING
from mcdreforged.api.rtext import RTextList, RText, RAction, RColor
from mcdreforged.api.command import Literal
from mcdreforged.api.decorator import new_thread

if TYPE_CHECKING:
    from mcdreforged.api.types import PluginServerInterface, Info, CommandSource, ServerInterface


bot_list = []
worlds = {
    "minecraft:overworld": "§a主世界",
    "minecraft:the_end": "§d末地",
    "minecraft:the_nether": "§4地狱",
}


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


def list_bot(server: 'ServerInterface'):
    new_list = []
    for bot in bot_list:
        new_list.append(get_player_pos(server, bot))
    return new_list


def msg_list_bot(server: 'ServerInterface'):
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
def send_bot_list(src: 'CommandSource'):
    src.reply(msg_list_bot(src.get_server()))


def on_player_joined(server: 'PluginServerInterface', player: str, info: 'Info'):
    joined_player = re.match(
        r"(\w+)\[([0-9\.\:\/]+|local)\] logged in with entity id", info.content
    )
    if joined_player:
        if joined_player.group(2) == "local":
            server.say("§7假人[" + player + "]加入了游戏")
            bot_list.append(player)


def on_player_left(server: 'PluginServerInterface', player):
    if player in bot_list:
        bot_list.remove(player)
        server.say("§7假人[" + player + "]离开了游戏")


def on_load(server: 'PluginServerInterface', old_module):
    global bot_list
    server.register_command(Literal("!!botlist").runs(send_bot_list))
    if old_module is not None:
        bot_list = old_module.bot_list


def on_server_startup(server: 'PluginServerInterface'):
    global bot_list
    bot_list = []
