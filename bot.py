import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
from discord.utils import format_dt
import datetime
import psutil
import asyncio
import json
import os

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"目前登入身份 --> {client.user.name}")
    await load_all_members()
    await update_status.start()

@tasks.loop(seconds=15)
async def update_status():
    total_members = 0
    for guild in client.guilds:
        total_members += guild.member_count

    status = f"{len(client.guilds)} 個伺服器  |  總人數 {total_members}"
    await client.change_presence(activity=discord.Game(name=status))

# 載入設定檔案
def ensure_settings():
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {"voice": []}
    except json.JSONDecodeError:
        # 如果檔案格式錯誤，我們就重新創建它
        settings = {"voice": []}

    # 確保 settings 是一個字典，且包含 "voice" 鍵
    if not isinstance(settings, dict):
        settings = {"voice": []}
    elif "voice" not in settings:
        settings["voice"] = []
    elif not isinstance(settings["voice"], list):
        # 如果 "voice" 的值不是列表，我們就重置它
        settings["voice"] = []

    # 保存更新後的設定，以修復任何問題
    save_settings(settings)
    return settings

def save_settings(settings):
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def update_server_state(guild_id, state):
    try:
        with open('server_states.json', 'r', encoding='utf-8') as f:
            states = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        states = {}

    states[guild_id] = state
    with open('server_states.json', 'w', encoding='utf-8') as f:
        json.dump(states, f, ensure_ascii=False, indent=4)

async def load_all_members():
    for guild in client.guilds:
        async for member in guild.fetch_members(limit=None):
            pass


@tree.command(name="語音通知", description="開啟或關閉伺服器的語音通知功能")
@app_commands.describe(action="選擇開啟或關閉")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(action=[
    app_commands.Choice(name="開啟", value="on"),
    app_commands.Choice(name="關閉", value="off")
])
async def voice_notification(interaction: discord.Interaction, action: app_commands.Choice[str]):
    try:
        guild_id = str(interaction.guild_id)
        settings = ensure_settings()

        # 根據動作添加或移除伺服器 ID
        if action.value == "on":
            if guild_id not in settings["voice"]:
                settings["voice"].append(guild_id)
                save_settings(settings)
                await interaction.response.send_message(
                    f"✅ 語音通知功能已開啟！\n\n"
                    f"你可以隨時使用 `/語音通知` 指令來切換此功能的狀態。\n"
                    f"目前狀態：開啟 ✅"
                )
            else:
                await interaction.response.send_message("❕ 語音通知功能已經是開啟狀態。")
        else:  # off
            if guild_id in settings["voice"]:
                settings["voice"].remove(guild_id)
                save_settings(settings)
                await interaction.response.send_message(
                    f"❎ 語音通知功能已關閉！\n\n"
                    f"你可以隨時使用 `/語音通知` 指令來切換此功能的狀態。\n"
                    f"目前狀態：關閉 ❎"
                )
            else:
                await interaction.response.send_message("❕ 語音通知功能已經是關閉狀態。")

        # 更新伺服器狀態
        update_server_state(guild_id, action.value)

    except Exception as e:
        print(f"❌ 在處理語音通知指令時發生錯誤：{str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ 發生錯誤：{str(e)}")
        else:
            await interaction.followup.send(f"❌ 發生錯誤：{str(e)}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('https://') and 'discord.com/channels' in message.content:
        link_parts = message.content.split('/')
        server_id = int(link_parts[-3])
        channel_id = int(link_parts[-2])
        message_id = int(link_parts[-1])
        guild = client.get_guild(server_id)
        channel = guild.get_channel(channel_id)
        linked_message = await channel.fetch_message(message_id)
        author = guild.get_member(linked_message.author.id)
        if author is None:
            embed_color = 0x2F3136
        else:
            author_highest_role = author.top_role
            embed_color = author_highest_role.color
        if linked_message.content:
            embed = discord.Embed(color=embed_color, description=linked_message.content)
            embed.set_author(name=linked_message.author.display_name,
                             url=linked_message.jump_url,
                             icon_url=linked_message.author.display_avatar.url)
            await message.channel.send(f"**{linked_message.author.name}** 在 <t:{int(linked_message.created_at.timestamp())}:F> 於 {linked_message.channel.mention} 發送了以下訊息:", embed=embed)
        if linked_message.embeds:
            await asyncio.sleep(0.5)
            for original_embed in linked_message.embeds:
                await message.channel.send(embed=original_embed)


@client.event
async def on_voice_state_update(member, before, after):
    try:
        settings = ensure_settings()
        guild_id = str(member.guild.id)

        if "voice" not in settings or guild_id not in settings["voice"]:
            return  # 如果伺服器不在列表中，就不做任何事

        state = get_server_state(guild_id)
        if state == "off":
            return  # 如果功能被關閉，就不做任何事

        if before.channel is None and after.channel is not None:  # 加入語音頻道
            timestamp = int(datetime.datetime.now().timestamp())
            channel = after.channel
            voice_channel_id = after.channel.id
            embed = discord.Embed(title="", description="", color=0x26FF2A)
            embed.add_field(name=':inbox_tray: 加入了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：<#{voice_channel_id}>`（{voice_channel_id}）`')
            await channel.send(embed=embed)
        elif before.channel is not None and after.channel is None:  # 離開語音頻道
            timestamp = int(datetime.datetime.now().timestamp())
            channel = before.channel
            voice_channel_id = before.channel.id
            embed = discord.Embed(title="", description="", color=0xFF0404)
            embed.add_field(name=':outbox_tray: 離開了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：<#{voice_channel_id}>`（{voice_channel_id}）`')
            await channel.send(embed=embed)
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:  # 切換語音頻道
            timestamp = int(datetime.datetime.now().timestamp())
            before_channel = before.channel
            after_channel = after.channel
            after_voice_channel_id = after.channel.id
            before_voice_channel_id = before.channel.id
            embed = discord.Embed(title="", description="", color=0x00bbff)
            embed.add_field(name=':outbox_tray: 切換了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：<#{before_voice_channel_id}>`（{before_voice_channel_id}）` \n已到：<#{after_voice_channel_id}>`（{after_voice_channel_id}）`')
            await before_channel.send(embed=embed)
            embed = discord.Embed(title="", description="", color=0x00bbff)
            embed.add_field(name=':inbox_tray: 切換了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：<#{after_voice_channel_id}>`（{after_voice_channel_id}）` \n已從：<#{before_voice_channel_id}>`（{before_voice_channel_id}）`')
            await after_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ 在處理語音狀態更新時發生錯誤：{str(e)}")

def get_server_state(guild_id):
    try:
        with open('server_states.json', 'r', encoding='utf-8') as f:
            states = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        states = {}

    return states.get(guild_id, "on")  # 如果沒有設定，預設為 "on"

@tree.command(name="指令列表", description="顯示該機器人的指令列表介面")
async def help_command(ctx):
    embed = discord.Embed(title="風暴機器人幫助介面", description="需要幫助嗎? 加入我們的 [Discord](https://discord.gg/daFQhVFGKj) 並開啟一個票單來與客服人員對談。", color=0x00bbff)
    
    embed.add_field(name="/用戶查詢", value="查詢用戶的帳號建立日期、加入日期和ID等", inline=True)
    embed.add_field(name="/頭貼查詢", value="查詢使用者的Discord個人頭貼", inline=True)
    embed.add_field(name="/伺服器資訊", value="查詢伺服器的創建日期、人數、伺服器ID和擁有者ID等", inline=True)
    embed.add_field(name="/身分組列表", value=" 查詢這個伺服器的所有身分組", inline=True)
    embed.add_field(name="/狀態", value="查詢目前機器人的延遲、CPU和RAM使用率、擁有者ID等", inline=True)
    embed.add_field(name="/邀請", value="取得這個機器人的邀請連結", inline=True)
    embed.add_field(name="/臨時語音 輸入密碼", value="輸入臨時語音頻道密碼", inline=True)
    embed.add_field(name="= = = = = = = = = = = = = = = = 下列為僅管理員操作的功能 = = = = = = = = = = = = = = = =", value=" ", inline=False)
    embed.add_field(name="/踢出", value="踢出指定用戶", inline=True)
    embed.add_field(name="/停權", value="停權指定用戶", inline=True)
    embed.add_field(name="/禁言", value="禁言指定用戶", inline=True)
    embed.add_field(name="/鎖定", value="鎖定指定頻道的輸入權限", inline=True)
    embed.add_field(name="/解除停權", value="解除停權指定用戶", inline=True)
    embed.add_field(name="/解除禁言", value="解除禁言指定用戶", inline=True)
    embed.add_field(name="/解除鎖定", value="解除鎖定指定頻道", inline=True)
    embed.add_field(name="/重建頻道", value="刪除並重建指定頻道", inline=True)
    embed.add_field(name="/臨時語音 建立", value="建立臨時語音通道", inline=True)
    embed.add_field(name="/臨時語音 移除", value="移除臨時語音通道", inline=True)






    await ctx.response.send_message(embed=embed)




@tree.command(name="踢出", description="將指定的成員從目前這個伺服器踢出")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定踢出的成員",
    reason="踢出的原因 (如果你不要寫原因的話這裡可以不用填)"
)
async def kick(ctx, user: discord.Member, *, reason: str = None):
        await user.kick(reason=reason)
        await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被踢出於本伺服器!**")

@tree.command(name="停權", description="將指定的成員從目前這個伺服器停權")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定停權的成員",
    reason="停權的原因 (如果你不要寫原因的話這裡可以不用填)"
)
async def kick(ctx, user: discord.Member, *, reason: str = None):
        await user.ban(reason=reason)
        await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被停權於本伺服器! :airplane:**")

@tree.command(name='禁言', description='禁言指定的成員 (他將在指定時間內無法打字或語音，重新進入伺服器也一樣)')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定禁言的成員",
    time="指定時間 (請使用秒數，若沒有填這一個的話預設將禁言一分鐘)",
    reason="禁言的原因 (如果你不要寫原因的話這裡可以不用填)"
)
async def timeout(ctx, user: discord.Member, time: int = 60, reason: str = None):

    duration_delta = datetime.timedelta(seconds=time)
    
    user = user or ctx.user

    await user.edit(timed_out_until=discord.utils.utcnow() + duration_delta, reason=f"已被 {ctx.user.name} 禁言，直到 {duration_delta} 後! 原因: {reason}")
    await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被禁言於本伺服器!**")

@tree.command(name='解除禁言', description='將已被禁言的成員解除禁言')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定解除禁言的成員"
)
async def untimeout(ctx, user: discord.Member):
    
    user = user or ctx.user
    
    await user.edit(timed_out_until=None)
    await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被解除禁言於本伺服器.**")

@tree.command(name="解除停權", description="將已被停權的成員解除停權.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    imput="將被停權的成員ID貼在這裡"
)
async def unban(ctx, imput: discord.User):
    await ctx.guild.unban(user=imput)
    await ctx.response.send_message(f":white_check_mark: <@{imput.id}> **已被解除停權於本伺服器!**")

@tree.command(name="鎖定", description="將指定的文字頻道文字輸入功能關閉使無權線的使用者無法打字")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="選擇一個要鎖定的文字頻道 (可以不填，預設為指令所輸入的那個頻道)"
)
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    
    overwrites = discord.PermissionOverwrite()
    overwrites.send_messages = False
    overwrites.create_public_threads = False
    overwrites.create_private_threads = False
    overwrites.send_messages_in_threads = False
    
    everyone_role = channel.guild.default_role
    
    await channel.set_permissions(everyone_role, overwrite=overwrites)
    
    await ctx.response.send_message(f":lock: <#{channel.id}> **已被鎖定**")

@tree.command(name="解除鎖定", description="將指定的文字頻道文字輸入功能開啟使無權線的使用者可以打字")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="選擇一個要解除鎖定的文字頻道 (可以不填，預設為指令所輸入的那個頻道)"
)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    
    # 重設 @everyone 角色的權限覆蓋
    overwrites = discord.PermissionOverwrite()
    overwrites.send_messages = None
    overwrites.create_public_threads = None
    overwrites.create_private_threads = None
    overwrites.send_messages_in_threads = None
    everyone_role = channel.guild.default_role
    await channel.set_permissions(everyone_role, overwrite=overwrites)
    
    await ctx.response.send_message(f":unlock: <#{channel.id}> **已被解除鎖定**")

@tree.command(name="用戶查詢", description="查詢使用者的Discord帳號建立日期、加入伺服器的日期、Discord ID等")
@app_commands.describe(
    user="選擇一個要查詢的用戶 (可以不填，預設為自己)"
)
async def user(ctx, user: discord.Member = None):
    if not user:
        user = ctx.user
    created_at = int(user.created_at.timestamp())
    joined_at = int(user.joined_at.timestamp())
    embed = discord.Embed(title="", description="", color=0x00bbff)
    embed.add_field(name="建立帳號的日期:", value=f"<t:{created_at}:R>", inline=True)
    embed.add_field(name="加入伺服器的日期:", value=f"<t:{joined_at}:R>", inline=True)
    embed.add_field(name="用戶ID:", value=f"{user.id}", inline=False)
    embed.set_thumbnail(url=user.display_avatar)
    await ctx.response.send_message(embed=embed)

@tree.command(name="頭貼查詢", description="查詢使用者的Discord頭貼")
@app_commands.describe(
    user="選擇一個要查詢的用戶 (可以不填，預設為自己)"
)
async def user(ctx, user: discord.Member = None):
    if not user:
        user = ctx.user
    embed = discord.Embed(title="", description=f"**[頭貼連結]({user.display_avatar})**", color=0x00bbff)
    embed.set_image(url=user.display_avatar)
    await ctx.response.send_message(embed=embed)

@tree.command(name="重建頻道", description="將文字頻道重新建立並刪除舊的頻道")
@app_commands.checks.has_permissions(administrator=True)
async def clear(ctx):
    if isinstance(ctx.channel, discord.TextChannel):
        new_channel = await ctx.channel.clone(reason="none")
        position = ctx.channel.position
        await new_channel.edit(position=position + 0)
        await ctx.channel.delete()
        await new_channel.send(f"**__頻道已被 <@{ctx.user.id}> 重建__**")

@tree.command(name="邀請", description="把我邀請製你的伺服器")
async def invite(ctx):
    embed = discord.Embed(title="連結列表", description="[點我把我邀進你的伺服器](https://discord.com/oauth2/authorize?client_id=1242816972304158820)\n[我們的官方伺服器](https://discord.gg/daFQhVFGKj)", color=0x3498DB)
    await ctx.response.send_message(embed=embed)

@tree.command(name="狀態", description="查詢機器人狀態")
async def status(ctx):
    latency = client.latency * 1000  # 將延遲轉換為毫秒
    cpu_percent = psutil.cpu_percent()
    owner_id = (await client.application_info()).owner.id
    total_members = 0
    for guild in client.guilds:
        total_members += guild.member_count
    embed = discord.Embed(title="機器人狀態", color=0x00ff00)
    embed.add_field(name="延遲", value=f"{latency:.2f} ms", inline=True)
    embed.add_field(name="CPU 使用率", value=f"{cpu_percent:.2f}%", inline=True)
    embed.add_field(name="RAM 使用率", value=f"{psutil.virtual_memory().percent}%", inline=True)
    embed.add_field(name="伺服器總數", value=f"**{len(client.guilds)}** 個伺服器", inline=True)
    embed.add_field(name="伺服器人數", value=f"**{total_members}** 個人", inline=True)
    embed.add_field(name="機器人擁有者", value=f"<@{owner_id}> ({owner_id})", inline=True)
    await ctx.response.send_message(embed=embed)


def get_verification_level_chinese(level: discord.VerificationLevel) -> str:
    levels = {
        discord.VerificationLevel.none: "無",
        discord.VerificationLevel.low: "低",
        discord.VerificationLevel.medium: "中",
        discord.VerificationLevel.high: "高",
        discord.VerificationLevel.highest: "最高",
    }
    level_name = levels.get(level, "未知")
    return f"{level_name}"


@tree.command(name="伺服器資訊", description="顯示此伺服器的相關資訊")
async def abc(interaction: discord.Interaction):
    guild = interaction.guild

    # 再次嘗試加載所有成員
    async for member in guild.fetch_members(limit=None):
        pass

    # 獲取人員數量
    member_count = guild.member_count

    # 使用多種方法識別機器人
    verified_bots = set()
    unverified_bots = set()

    for member in guild.members:
        if member.bot:
            verified_bots.add(member)
        elif getattr(member.public_flags, 'verified_bot', False):
            verified_bots.add(member)
        elif getattr(member, 'application_id', None) is not None:
            unverified_bots.add(member)
        elif discord.utils.get(member.roles, name="Bots") is not None:
            unverified_bots.add(member)

    # 特殊處理：檢查成員的公開標誌
    for member in guild.members:
        flags = member.public_flags.value
        if flags & (1 << 16):  # BOT_HTTP_INTERACTIONS flag
            if member not in verified_bots and member not in unverified_bots:
                unverified_bots.add(member)

    verified_bot_count = len(verified_bots)
    unverified_bot_count = len(unverified_bots)
    bot_count = verified_bot_count + unverified_bot_count
    human_count = member_count - bot_count

    # 列出所有機器人的資訊
    bot_info = "機器人列表:\n"
    for bot in verified_bots:
        bot_info += f"✅ {bot.name} (ID: {bot.id})\n"
    for bot in unverified_bots:
        bot_info += f"❓ {bot.name} (ID: {bot.id})\n"

    # 其餘的代碼保持不變...
    text_channel_count = len(guild.text_channels)
    voice_channel_count = len(guild.voice_channels)
    total_channel_count = text_channel_count + voice_channel_count

    role_count = len(guild.roles) - 1
    admin_role_count = len([role for role in guild.roles if role.permissions.administrator])
    non_admin_role_count = role_count - admin_role_count

    created_at = int(guild.created_at.timestamp())
    boost_count = guild.premium_subscription_count
    
    # 獲取並轉換驗證等級為中文
    verification_level = get_verification_level_chinese(guild.verification_level)
    
    owner_id = guild.owner_id

    embed = discord.Embed(title=f"{guild.name} 的伺服器資訊", color=discord.Color.green())
    embed.add_field(name="伺服器ID", value=f"{guild.id}", inline=False)
    embed.add_field(name="伺服器擁有者ID", value=str(owner_id), inline=True)
    embed.add_field(name="伺服器創建日期", value=f"<t:{created_at}:F>", inline=False)
    embed.add_field(name="伺服器人數", value=f"總人數: {member_count}\n真人: {human_count}\n機器人: {bot_count}", inline=True)
    embed.add_field(name="伺服器頻道數", value=f"總頻道數: {total_channel_count}\n文字頻道: {text_channel_count}\n語音頻道: {voice_channel_count}", inline=True)
    embed.add_field(name="伺服器身分組數", value=f"總身分組數: {role_count}\n有管理員權限: {admin_role_count}\n沒有管理員權限: {non_admin_role_count}", inline=True)
    embed.add_field(name="伺服器加成數", value=str(boost_count), inline=True)
    embed.add_field(name="伺服器驗證等級", value=verification_level, inline=True)
    embed.add_field(name="身分組列表", value="請使用  /身分組列表", inline=True)

    await interaction.response.send_message(embed=embed)


@tree.command(name="身分組列表", description="列出此伺服器的所有身分組")
async def role_list(ctx):
    guild = ctx.guild
    roles = [f"`{role.name}`" for role in guild.roles[1:]]
    role_list_str = " | ".join(roles)

    embed = discord.Embed(title=f"身分組列表", description=role_list_str, color=discord.Color.green())
    await ctx.response.send_message(embed=embed)

class TempVoiceClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

class 臨時語音(app_commands.Group):
    ...
temp_voice = 臨時語音(name="臨時語音")
tree.add_command(temp_voice)

class SetPasswordButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="設定密碼", custom_id="set_password")

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if not user.voice:
            await interaction.response.send_message("你必須在一個語音頻道中才能設定密碼。", ephemeral=True)
            return

        guild = interaction.guild
        file_path = f'temp_voice/{guild.id}.json'
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if user.voice.channel.id not in data['temp_channels']:
            await interaction.response.send_message("你必須在你創建的臨時語音頻道中才能設定密碼。", ephemeral=True)
            return

        modal = PasswordModal(user.voice.channel)
        await interaction.response.send_modal(modal)

class PasswordModal(discord.ui.Modal):
    def __init__(self, voice_channel):
        super().__init__(title="設定語音頻道密碼")
        self.voice_channel = voice_channel
        self.password = discord.ui.TextInput(label="密碼", placeholder="輸入 'none' 表示無密碼", required=True)
        self.add_item(self.password)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        file_path = f'temp_voice/{guild.id}.json'
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        password = self.password.value.lower()
        
        if password == 'none':
            if str(self.voice_channel.id) in data.get('passwords', {}):
                del data['passwords'][str(self.voice_channel.id)]
            await self.voice_channel.set_permissions(guild.default_role, connect=True)
            await interaction.response.send_message("密碼已移除。", ephemeral=True)
        else:
            if 'passwords' not in data:
                data['passwords'] = {}
            data['passwords'][str(self.voice_channel.id)] = password
            await self.voice_channel.set_permissions(guild.default_role, connect=False)
            await self.voice_channel.set_permissions(interaction.user, connect=True)
            await interaction.response.send_message("密碼已設定。", ephemeral=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f)

@temp_voice.command(name="建立", description="建立臨時語音通道")
@app_commands.describe(
    voice_channel="設定臨時語音的語音頻道",
    text_channel="設定臨時語音面板位置"
)
@app_commands.checks.has_permissions(administrator=True)
async def create(interaction: discord.Interaction, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel):
    guild = interaction.guild
    
    if not os.path.exists('temp_voice'):
        os.makedirs('temp_voice')
    
    file_path = f'temp_voice/{guild.id}.json'
    data = {}
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    
    category = await guild.create_category('臨時語音')
    
    data['voice_channel_id'] = voice_channel.id
    data['text_channel_id'] = text_channel.id
    data['category_id'] = category.id
    data['temp_channels'] = []
    
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    await voice_channel.edit(user_limit=1)
    await text_channel.set_permissions(guild.default_role, send_messages=False)
    
    view = discord.ui.View()
    view.add_item(SetPasswordButton())
    await text_channel.send("點擊下方按鈕來設定語音頻道密碼：", view=view)
    
    await interaction.response.send_message("臨時語音系統已設置完成。", ephemeral=True)

@temp_voice.command(name="輸入密碼", description="輸入臨時語音頻道設定的密碼")
@app_commands.describe(
    voice_channel="要加入的語音頻道",
    password="頻道密碼"
)
async def 輸入臨時語音頻道密碼(interaction: discord.Interaction, voice_channel: discord.VoiceChannel, password: str):
    guild = interaction.guild
    file_path = f'temp_voice/{guild.id}.json'
    
    if not os.path.exists(file_path):
        await interaction.response.send_message("臨時語音系統尚未設置。", ephemeral=True)
        return
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if str(voice_channel.id) not in data.get('passwords', {}):
        await interaction.response.send_message("此頻道未設定密碼。", ephemeral=True)
        return
    
    if data['passwords'][str(voice_channel.id)] == password:
        await voice_channel.set_permissions(interaction.user, connect=True)
        await interaction.response.send_message("密碼正確，你現在可以加入該語音頻道。", ephemeral=True)
    else:
        await interaction.response.send_message("密碼錯誤。", ephemeral=True)

@client.event
async def temp_on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        return

    guild = member.guild
    file_path = f'temp_voice/{guild.id}.json'
    
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if after.channel and after.channel.id == data['voice_channel_id']:
        category = discord.utils.get(guild.categories, id=data['category_id'])
        new_channel = await category.create_voice_channel(name=f"{member.name}的頻道")
        
        await member.move_to(new_channel)
        
        await new_channel.set_permissions(member, 
            manage_channels=True,
            manage_permissions=True,
            manage_webhooks=True,
            create_instant_invite=True,
            connect=True,
            speak=True,
            stream=True,
            use_voice_activation=True,
            priority_speaker=True,
            mute_members=True,
            deafen_members=True,
            move_members=True,
            use_embedded_activities=True
        )
        
        data['temp_channels'].append(new_channel.id)
        with open(file_path, 'w') as f:
            json.dump(data, f)
    
    if before.channel and before.channel.id in data['temp_channels']:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            data['temp_channels'].remove(before.channel.id)
            if 'passwords' in data and str(before.channel.id) in data['passwords']:
                del data['passwords'][str(before.channel.id)]
            with open(file_path, 'w') as f:
                json.dump(data, f)

@temp_voice.command(name="移除", description="移除臨時語音通道")
@app_commands.checks.has_permissions(administrator=True)
async def 刪除臨時語音系統(interaction: discord.Interaction):
    guild = interaction.guild
    file_path = f'temp_voice/{guild.id}.json'
    
    if os.path.exists(file_path):
        # 刪除 JSON 文件
        os.remove(file_path)
        await interaction.response.send_message("臨時語音系統設置已被移除。請注意，相關的頻道和分類並未被刪除。", ephemeral=True)
    else:
        await interaction.response.send_message("此伺服器沒有臨時語音系統的設置文件。", ephemeral=True)
        
client.run("機器人Token貼這裡")
