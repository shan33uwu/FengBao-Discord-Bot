import discord
from discord.ext import commands
from discord import app_commands
import psutil

class Info(commands.GroupCog, name="info", description="查詢資訊功能 ( 使用 **/info help** 即可查看使用說明 ) "):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name="help", description="顯示所有可用的指令")
    async def help(self, interaction: discord.Interaction):
        help_embed = discord.Embed(title="查詢資訊使用說明", description="", color=discord.Color.blue())

        help_embed.add_field(name="/info user", value="查詢用戶資訊", inline=False)
        help_embed.add_field(name="/info avatar", value="查詢用戶的頭像", inline=False)
        help_embed.add_field(name="/info bot", value="查詢機器人狀態", inline=False)
        help_embed.add_field(name="/info server", value="""查詢伺服器資訊""", inline=False)
        help_embed.add_field(name="/info roles", value="""列出此伺服器的所有身分組""", inline=False)
        await interaction.response.send_message(embed=help_embed)

    @app_commands.command(name="user", description="查詢用戶資訊")
    @app_commands.describe(
        user="選擇一個用戶 (選填)"
    )
    async def user(self, interaction: discord.Interaction, user: discord.Member = None):
        if not user:
            user = interaction.user
        created_at = int(user.created_at.timestamp())
        joined_at = int(user.joined_at.timestamp())
        embed = discord.Embed(title="", description="", color=0x00bbff)
        embed.add_field(name="建立帳號的日期:", value=f"<t:{created_at}:R>", inline=True)
        embed.add_field(name="加入伺服器的日期:", value=f"<t:{joined_at}:R>", inline=True)
        embed.add_field(name="用戶ID:", value=f"{user.id}", inline=False)
        embed.set_thumbnail(url=user.display_avatar)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="查詢用戶的頭像")
    @app_commands.describe(
        user="選擇一個用戶 (選填)"
    )
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        if user is None:
            user = interaction.user
        embed = discord.Embed(title=f"{user.name}的頭像", color=discord.Color.blue())
        embed.set_image(url=user.display_avatar.url)
        avatar_sizes = {
            "128x128": user.display_avatar.replace(size=128).url,
            "256x256": user.display_avatar.replace(size=256).url,
            "1024x1024": user.display_avatar.replace(size=1024).url
        }
        for size, url in avatar_sizes.items():
            embed.add_field(name=" ", value=f"[{size}]({url})", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bot", description="查詢機器人狀態")
    async def status(self, interaction: discord.Interaction):
        latency = self.bot.latency * 1000  # 將延遲轉換為毫秒
        cpu_percent = psutil.cpu_percent()
        owner_id = (await self.bot.application_info()).owner.id
        total_members = 0
        for guild in self.bot.guilds:
            total_members += guild.member_count
        embed = discord.Embed(title="機器人狀態", color=discord.Color.blue())
        embed.add_field(name="延遲", value=f"{latency:.2f} ms", inline=True)
        embed.add_field(name="CPU 使用率", value=f"{cpu_percent:.2f}%", inline=True)
        embed.add_field(name="RAM 使用率", value=f"{psutil.virtual_memory().percent}%", inline=True)
        embed.add_field(name="伺服器總數", value=f"**{len(self.bot.guilds)}** 個伺服器", inline=True)
        embed.add_field(name="伺服器人數", value=f"**{total_members}** 個人", inline=True)
        embed.add_field(name="機器人擁有者", value=f"<@{owner_id}> ({owner_id})", inline=True)
        await interaction.response.send_message(embed=embed)

    def get_verification_level_chinese(self, level: discord.VerificationLevel) -> str:
        levels = {
            discord.VerificationLevel.none: "無",
            discord.VerificationLevel.low: "低",
            discord.VerificationLevel.medium: "中",
            discord.VerificationLevel.high: "高",
            discord.VerificationLevel.highest: "最高",
        }
        level_name = levels.get(level, "未知")
        return f"{level_name}"

    @app_commands.command(name="server", description="查詢伺服器資訊")
    async def server(self, interaction: discord.Interaction):
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
        verification_level = self.get_verification_level_chinese(guild.verification_level)
        
        owner_id = guild.owner_id

        embed = discord.Embed(title=f"{guild.name} 的伺服器資訊", color=discord.Color.blue())
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

    @app_commands.command(name="roles", description="列出此伺服器的所有身分組")
    async def role_list(self, interaction: discord.Interaction):
        guild = interaction.guild
        roles = [f"`{role.name}`" for role in guild.roles[1:]]
        role_list_str = " | ".join(roles)

        embed = discord.Embed(title=f"身分組列表", description=role_list_str, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
