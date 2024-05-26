import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
from discord.utils import format_dt
import datetime
import psutil
import asyncio


intents = discord.Intents.default()
intents.voice_states = True
intents.typing = False
intents.presences = False
intents.message_content = True
intents.members = False

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"目前登入身份 --> {client.user.name}")
    await update_status.start()

@tasks.loop(seconds=15)
async def update_status():
    total_members = 0
    for guild in client.guilds:
        total_members += guild.member_count

    status = f"{len(client.guilds)} 個伺服器  |  總人數 {total_members}"
    await client.change_presence(activity=discord.Game(name=status))

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
    if before.channel is None and after.channel is not None:  # 加入語音頻道
        timestamp = int(datetime.datetime.now().timestamp())
        channel = after.channel
        voice_channel_id = after.channel.id
        embed = discord.Embed(title="", description="", color=0x26FF2A)
        embed.add_field(name=':inbox_tray: 加入了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：{after.channel.mention}`（{voice_channel_id}）`')
        await channel.send(embed=embed)
    elif before.channel is not None and after.channel is None:  # 離開語音頻道
        timestamp = int(datetime.datetime.now().timestamp())
        channel = before.channel
        voice_channel_id = before.channel.id
        embed = discord.Embed(title="", description="", color=0xFF0404)
        embed.add_field(name=':outbox_tray: 離開了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：{before.channel.mention}`（{voice_channel_id}）`')
        await channel.send(embed=embed)
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:  # 切換語音頻道
        timestamp = int(datetime.datetime.now().timestamp())
        before_channel = before.channel
        after_channel = after.channel
        after_voice_channel_id = after.channel.id
        before_voice_channel_id = before.channel.id
        embed = discord.Embed(title="", description="", color=0x00bbff)
        embed.add_field(name=':outbox_tray: 切換了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：{before.channel.mention}`（{before_voice_channel_id}）` \n已到：{after.channel.mention}`（{after_voice_channel_id}）`')
        await before_channel.send(embed=embed)
        embed = discord.Embed(title="", description="", color=0x00bbff)
        embed.add_field(name=':inbox_tray: 切換了語音頻道', value=f'時間：<t:{timestamp}><t:{timestamp}:R> \n用戶：{member.mention}`（{member.name}）` \n頻道：{after.channel.mention}`（{after_voice_channel_id}）` \n已從：{before.channel.mention}`（{before_voice_channel_id}）`')
        await after_channel.send(embed=embed)

@tree.command(name="幫助", description="顯示該機器人的幫助介面")
async def help_command(ctx):
    embed = discord.Embed(title="風暴機器人幫助介面", description="需要幫助嗎? 加入我們的 [Discord](https://discord.gg/daFQhVFGKj) 並開啟一個票單來與客服人員對談。", color=0x00bbff)
    embed.add_field(name="機器人說明", value="""本機器人由 weiwei_hacking 與 [claude.ai](https://claude.ai/) 開發並製作完成
                                                            且本機器人以完全公開開源的方式向公眾發布，你可以加入我們的 [Discord](https://discord.gg/daFQhVFGKj) 來獲取檔案。""", inline=False)
    embed.add_field(name="機器人指令權限說明", value="""功能指令的說明前面如果含有這個🛠️emoji即代表該指令僅限擁有管理員權限的使用者使用
                                                                       如果是含有這個👑emoji即代表該指令僅限機器人擁有者使用
                                                                       如果都沒有都沒有上述兩個emoji的話即代表所有人皆可使用。""", inline=False)
    embed.add_field(name="指令列表", value="`/幫助\n/用戶查詢\n/頭貼查詢\n/邀請\n/踢出\n/停權\n/解除停權\n/禁言\n/解除禁言\n/鎖定\n/解除鎖定\n/清除頻道\n/重建頻道\n/狀態\n/伺服器資訊`", inline=False)
    await ctx.response.send_message(embed=embed)

@tree.command(name="踢出", description="🛠️ ▏將指定的成員從目前這個伺服器踢出")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定踢出的成員",
    reason="踢出的原因 (如果你不要寫原因的話這裡可以不用填)"
)
async def kick(ctx, user: discord.Member, *, reason: str = None):
        await user.kick(reason=reason)
        await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被踢出於本伺服器!**")

@tree.command(name="停權", description="🛠️ ▏將指定的成員從目前這個伺服器停權")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定停權的成員",
    reason="停權的原因 (如果你不要寫原因的話這裡可以不用填)"
)
async def kick(ctx, user: discord.Member, *, reason: str = None):
        await user.ban(reason=reason)
        await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被停權於本伺服器! :airplane:**")

@tree.command(name='禁言', description='🛠️ ▏禁言指定的成員 (他將在指定時間內無法打字或語音，重新進入伺服器也一樣)')
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

@tree.command(name='解除禁言', description='🛠️ ▏將已被禁言的成員解除禁言')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個你要指定解除禁言的成員"
)
async def untimeout(ctx, user: discord.Member):
    
    user = user or ctx.user
    
    await user.edit(timed_out_until=None)
    await ctx.response.send_message(f":white_check_mark: <@{user.id}> **已被解除禁言於本伺服器.**")

@tree.command(name="解除停權", description="🛠️ ▏將已被停權的成員解除停權.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    imput="將被停權的成員ID貼在這裡"
)
async def unban(ctx, imput: discord.User):
    await ctx.guild.unban(user=imput)
    await ctx.response.send_message(f":white_check_mark: <@{imput.id}> **已被解除停權於本伺服器!**")

@tree.command(name="鎖定", description="🛠️ ▏將指定的文字頻道文字輸入功能關閉使無權線的使用者無法打字")
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

@tree.command(name="解除鎖定", description="🛠️ ▏將指定的文字頻道文字輸入功能開啟使無權線的使用者可以打字")
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


@tree.command(name="清除頻道", description="🛠️ ▏清除文字頻道的字串")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    number_of_message="輸入指定的清理數量 (不要太多，以免造成機器人API限速)"
)
async def clear(ctx, number_of_message: int):
    await ctx.response.send_message(f":white_check_mark: **頻道清理中**")
    
    channel = ctx.channel

    deleted = await channel.purge(limit=number_of_message+1)

    await ctx.channel.send(f"```js\n{len(deleted)} 條訊息已被刪除```")

@tree.command(name="重建頻道", description="🛠️ ▏將文字頻道重新建立並刪除舊的頻道")
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

@tree.command(name="伺服器資訊", description="顯示此伺服器的相關資訊")
async def abc(ctx):
    guild = ctx.guild

    # 獲取人員數量
    member_count = len(guild.members)
    bot_count = len([m for m in guild.members if m.bot])
    human_count = member_count - bot_count

    # 獲取頻道數量
    text_channel_count = len(guild.text_channels)
    voice_channel_count = len(guild.voice_channels)
    total_channel_count = text_channel_count + voice_channel_count

    # 獲取身分組數量
    role_count = len(guild.roles) - 1  # 減去 @everyone 身分組
    admin_role_count = len([role for role in guild.roles if role.permissions.administrator])
    non_admin_role_count = role_count - admin_role_count

    # 其他伺服器資訊
    created_at = int(guild.created_at.timestamp())
    boost_count = guild.premium_subscription_count
    verification_level = str(guild.verification_level)
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

    await ctx.response.send_message(embed=embed)

@tree.command(name="身分組列表", description="列出此伺服器的所有身分組")
async def role_list(ctx):
    guild = ctx.guild
    roles = [f"`{role.name}`" for role in guild.roles[1:]]
    role_list_str = " | ".join(roles)

    embed = discord.Embed(title=f"身分組列表", description=role_list_str, color=discord.Color.green())
    await ctx.response.send_message(embed=embed)
    
client.run("機器人Token貼這裡")