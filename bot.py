import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
from discord.utils import format_dt
import datetime
import psutil
import asyncio

intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"機器人上線了! 登入的機器人身份 --> {client.user.name}")

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
        embed_color = linked_message.author.top_role.color
        if linked_message.content:
            embed = discord.Embed(color=embed_color, description=linked_message.content)
            embed.set_author(name=linked_message.author.display_name,
                             url=linked_message.jump_url,
                             icon_url=linked_message.author.display_avatar.url)
            await message.channel.send(f"**{linked_message.author.mention}** 在 <t:{int(linked_message.created_at.timestamp())}:F> 於 {linked_message.channel.mention} 發送了以下訊息:", embed=embed,silent = True,allowed_mentions=discord.AllowedMentions.none())
        if linked_message.embeds:
            await asyncio.sleep(0.5)
            for original_embed in linked_message.embeds:
                await message.channel.send(embed=original_embed)

@client.event
async def on_voice_state_update(member, before, after):
    try:
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


class Info(app_commands.Group):
    ...
info = Info(name="info")
tree.add_command(info)


@tree.command(name="kick", description="把成員從這個伺服器踢出")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個用戶",
    reason="踢出原因 (選填)"
)
async def kick(ctx, user: discord.Member, *, reason: str = "無原因"):
        await user.kick(reason=reason)
        embed = discord.Embed (title="📢 有人被管理員踢出了", description=f"<@{user.id}> 因 **{reason}** 被踢出了", color=0xFF0000)
        await ctx.response.send_message(embed=embed)

@tree.command(name="ban", description="把成員從這個伺服器停權")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個用戶",
    reason="停權原因 (選填)"
)
async def ban(ctx, user: discord.Member, *, reason: str = "無原因"):
        await user.ban(reason=reason)
        embed = discord.Embed (title="📢 有人被管理員停權了", description=f"<@{user.id}> 因 **{reason}** 被踢出了", color=0xFF0000)
        await ctx.response.send_message(embed=embed)

@tree.command(name="timeout", description="把成員從這個伺服器禁言")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個用戶",
    time="禁言秒數，如果超過1分鐘請一律使用秒數表達",
    reason="禁言原因 (選填)"
)
async def timeout(ctx, user: discord.Member, time: int = 60, reason: str = "無原因"):
        duration_delta = datetime.timedelta(seconds=time)
        user = user or ctx.user
        await user.edit(timed_out_until=discord.utils.utcnow() + duration_delta, reason=f"已被 {ctx.user.name} 禁言，直到 {duration_delta} 後! 原因: {reason}")
        embed = discord.Embed (title="📢 有人被管理員禁言了", description=f"<@{user.id}> 因 **{reason}** 被禁言了，直到 **{duration_delta}** 秒後", color=0xFF0000)
        await ctx.response.send_message(embed=embed)

@tree.command(name='untimeout', description='把被禁言的成員解除禁言')
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    user="選擇一個用戶"
)
async def untimeout(ctx, user: discord.Member):
    user = user or ctx.user
    await user.edit(timed_out_until=None)
    embed = discord.Embed (title="📢 有人被管理員解除禁言了", description=f"<@{user.id}> 的禁言已被解除", color=0x00FF00)
    await ctx.response.send_message(embed=embed)

@tree.command(name="unban", description="把被停權的成員解除禁言.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    imput="輸入一個被停權的使用者ID"
)
async def unban(ctx, imput: discord.User):
    await ctx.guild.unban(user=imput)
    embed = discord.Embed (title="📢 有人被管理員解除停權了", description=f"<@{imput.id}> 的停權已被解除", color=0x00FF00)
    await ctx.response.send_message(embed=embed)

@tree.command(name="lock", description="鎖定當前或指定文字頻道使成員無法發送訊息")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="選擇一個頻道 (選填)"
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
    embed = discord.Embed (title="📢 有頻道被管理員鎖定了", description=f"<#{channel.id}> 已被鎖定", color=0xFF0000)
    await ctx.response.send_message(embed=embed)

@tree.command(name="unlock", description="解除鎖定當前或指定文字頻道使成員可以發送訊息")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="選擇一個頻道 (選填)"
)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    overwrites = discord.PermissionOverwrite()
    overwrites.send_messages = None
    overwrites.create_public_threads = None
    overwrites.create_private_threads = None
    overwrites.send_messages_in_threads = None
    everyone_role = channel.guild.default_role
    await channel.set_permissions(everyone_role, overwrite=overwrites)
    embed = discord.Embed (title="📢 有頻道被管理員解除鎖定了", description=f"<#{channel.id}> 已被解除鎖定", color=0x00FF00)
    await ctx.response.send_message(embed=embed)

@info.command(name="user", description="查詢用戶資訊")
@app_commands.describe(
    user="選擇一個用戶 (選填)"
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

@info.command(name="avatar", description="查詢用戶的頭像")
@app_commands.describe(
    user="選擇一個用戶 (選填)"
)
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user
    embed = discord.Embed(title=f"{user.name}的頭像", color=0x00ff00)
    embed.set_image(url=user.display_avatar.url)
    avatar_sizes = {
        "128x128": user.display_avatar.replace(size=128).url,
        "256x256": user.display_avatar.replace(size=256).url,
        "1024x1024": user.display_avatar.replace(size=1024).url
    }
    for size, url in avatar_sizes.items():
        embed.add_field(name=f" ", value=f"[{size}]({url})", inline=True)
    await interaction.response.send_message(embed=embed)

@info.command(name="bot", description="查詢機器人狀態")
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

@info.command(name="server", description="查詢伺服器資訊")
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

    embed = discord.Embed(title=f"{guild.name} 的伺服器資訊", color=0x00ff00)
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

@info.command(name="role_list", description="列出此伺服器的所有身分組")
async def role_list(ctx):
    guild = ctx.guild
    roles = [f"`{role.name}`" for role in guild.roles[1:]]
    role_list_str = " | ".join(roles)

    embed = discord.Embed(title=f"身分組列表", description=role_list_str, color=discord.Color.green())
    await ctx.response.send_message(embed=embed)

@tree.command(name="nuke", description="刪除當前頻道並以相同名稱及設置重建一個")
@app_commands.checks.has_permissions(administrator=True)
async def nuke(ctx):
    if isinstance(ctx.channel, discord.TextChannel):
        new_channel = await ctx.channel.clone(reason="none")
        position = ctx.channel.position
        await new_channel.edit(position=position + 0)
        await ctx.channel.delete()
        embed = discord.Embed (title="📢 該頻道被管理員重建了", description=f"<@{ctx.user.id}> 重建了這個頻道", color=0x00FF00)
        await new_channel.send(embed=embed)

@tree.command(name="invite", description="查詢機器人邀請連結")
async def invite(ctx):
    embed = discord.Embed(title="歡迎使用風暴機器人，這是我們的邀請連結", description="[點我邀請風暴機器人](https://discord.com/oauth2/authorize?client_id=1242816972304158820)\n[點我進入官方伺服器](https://discord.gg/daFQhVFGKj)", color=0x00ff00)
    await ctx.response.send_message(embed=embed)



client.run("TOKEN貼這裡喔!")
