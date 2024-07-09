import discord
import datetime
from discord import app_commands
from discord.ext import commands

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="停權使用者")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(
        member="選擇一個用戶",
        reason="停權原因 (選填)"
    )
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無"):
        if interaction.user.top_role <= member.top_role:
            await interaction.response.send_message("你沒有權限停權這個用戶!", ephemeral=True)
            return
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} 已被停權。原因: {reason}")

    @app_commands.command(name="kick", description="踢出使用者")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(
        member="選擇一個用戶",
        reason="踢出原因 (選填)"
    )
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無"):
        if interaction.user.top_role <= member.top_role:
            await interaction.response.send_message("你沒有權限踢出這個用戶!", ephemeral=True)
            return
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} 已被踢出。原因: {reason}")

    @app_commands.command(name="timeout", description="禁言使用者")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        member="選擇一個用戶",
        time="禁言秒數",
        reason="禁言原因 (選填)"
    )
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, time: int = 60, reason: str = "無"):
        duration_delta = datetime.timedelta(seconds=time)
        await member.edit(timed_out_until=discord.utils.utcnow() + duration_delta, reason=f"已被 {interaction.user.name} 禁言，直到 {duration_delta} 後! 原因: {reason}")
        await interaction.response.send_message(f"{member.mention} 已被禁言，直到 **{duration_delta}** 後。原因: {reason}")

    @app_commands.command(name='untimeout', description='把被禁言的成員解除禁言')
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        member="選擇一個用戶"
    )
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        await member.edit(timed_out_until=None)
        await interaction.response.send_message(f"{member.mention} 已被解除禁言")

    @app_commands.command(name="unban", description="把被停權的成員解除停權")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        user="輸入一個被停權的使用者ID"
    )
    async def unban(self, interaction: discord.Interaction, user: discord.User):
        await interaction.guild.unban(user=user)
        await interaction.response.send_message(f"{user.mention} 已被解除停權")

    @app_commands.command(name="nuke", description="刪除當前頻道並以相同名稱及設置重建一個")
    @app_commands.default_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.TextChannel):
            new_channel = await interaction.channel.clone(reason="none")
            position = interaction.channel.position
            await new_channel.edit(position=position)
            await interaction.channel.delete()
            await new_channel.send(f"頻道已被 <@{interaction.user.id}> 重建")

    @app_commands.command(name="lock", description="鎖定當前或指定文字頻道使成員無法發送訊息")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="選擇一個頻道 (選填)"
    )
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        overwrites = discord.PermissionOverwrite()
        overwrites.send_messages = False
        overwrites.create_public_threads = False
        overwrites.create_private_threads = False
        overwrites.send_messages_in_threads = False
        everyone_role = channel.guild.default_role
        await channel.set_permissions(everyone_role, overwrite=overwrites)
        await interaction.response.send_message(f"頻道已被 <@{interaction.user.id}> 鎖定")

    @app_commands.command(name="unlock", description="解除鎖定當前或指定文字頻道使成員可以發送訊息")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="選擇一個頻道 (選填)"
    )
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        overwrites = discord.PermissionOverwrite()
        overwrites.send_messages = None
        overwrites.create_public_threads = None
        overwrites.create_private_threads = None
        overwrites.send_messages_in_threads = None
        everyone_role = channel.guild.default_role
        await channel.set_permissions(everyone_role, overwrite=overwrites)
        embed = discord.Embed (title="📢 有頻道被管理員解除鎖定了", description=f"<#{channel.id}> 已被解除鎖定", color=0x00FF00)
        await interaction.response.send_message(f"頻道已被 <@{interaction.user.id}> 解除鎖定")


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
