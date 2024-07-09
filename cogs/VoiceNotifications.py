import discord
from discord.ext import commands
import datetime

class VoiceNotifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
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

async def setup(bot):
    await bot.add_cog(VoiceNotifications(bot))