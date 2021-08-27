from mcdr_plugin_panel.network.data_packer import MessageType
import re
from mcdreforged.api.types import PluginServerInterface, Info, CommandSource
from mcdreforged.api.rtext import RTextList, RText, RAction, RColor
from mcdreforged.api.command import Literal
from mcdreforged.api.decorator import new_thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcdr_plugin_panel.api.types import EventInfo, GroupInterface
    from mcdreforged.api.types import ServerInterface

bot_list = []
player_list = []


worlds = {
    "minecraft:overworld": RText("主世界", RColor.green),
    "minecraft:the_end": RText("末地", RColor.light_purple),
    "minecraft:the_nether": RText("地狱", RColor.red),
}

# 公共方法


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


# 服务器部分


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


# 面板部分


def get_group():
    from mcdr_plugin_panel.api.components import Table, Group, Button

    group = (
        Group("carpetbotlist", "假人列表")
        .with_component(Button("refresh", "刷新"))
        .with_component(
            Table("bot_list")
            .with_column("name", "假人名称")
            .with_column("pos", "假人坐标")
            .with_column("dimension", "假人维度")
            .with_component(Button("kill", "下线"))
        )
    )

    return group


@new_thread("send_bot_list_to_panel")
def send_bot_list_to_panel(server: "ServerInterface", panel: "GroupInterface"):
    panel.send_message(MessageType.INFO, "假人列表刷新中")
    data = list_bot(server)
    data = [
        {
            "pos": f"({d['x']}, {d['y']}, {d['z']})",
            "dimension": worlds[d["dimension"]].to_json_object(),
            "name": d["player"],
        }
        for d in data
    ]
    server.logger.info("发送假人数据")
    panel.send_data("bot_list", data)
    panel.send_message(MessageType.SUCCESS, "假人列表刷新成功")


def kill_bot(server: "ServerInterface", panel: "GroupInterface", bot_name):
    server.execute(f"player {bot_name} kill")
    panel.send_message(MessageType.SUCCESS, f"下线假人 [{bot_name}]")


def event_handler(
    server: "ServerInterface", panel: "GroupInterface", info: "EventInfo"
):
    if info.event == "kill":
        bot_name = info.content[0]["name"]
        kill_bot(server, panel, bot_name)
    elif info.event == "refresh":
        send_bot_list_to_panel(server, panel)


# MCDR事件


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
    panel = server.get_plugin_instance("mcdr_plugin_panel")
    panel.register(get_group(), event_handler)
    server.register_command(Literal("!!botlist").runs(lambda src: send_bot_list(src)))
    if old_module is not None:
        bot_list = old_module.bot_list
        player_list = old_module.player_list


def on_unload(server: PluginServerInterface):
    panel = server.get_plugin_instance("mcdr_plugin_panel")
    panel.unregister("carpetbotlist")


def on_server_startup(server):
    global bot_list, player_list
    bot_list = []
    player_list = []
