import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class TemporaryVoice(commands.GroupCog, name="temp_voice", description="臨時語音功能 ( 使用 **/temp_voice help** 即可查看使用說明 ) "):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="顯示所有可用的指令")
    async def help(self, interaction: discord.Interaction):
        help_embed = discord.Embed(title="臨時語音系統使用說明", description="", color=discord.Color.blue())

        help_embed.add_field(name="/temp_voice create {voice_channel} {text_channel}", value="""**`使用這個指令前你需要有管理員權限`**
                                                                                                       > 第一個變數設置為你要開啟臨時語音的通道
                                                                                                       > 第二個變數設置為你要顯示臨時語音面板的頻道""", inline=False)
        help_embed.add_field(name="/temp_voice remove", value="""**`使用這個指令前你需要有管理員權限`**
                                                                        > 使用後會把這個伺服器的臨時語音系統移除""", inline=False)
        help_embed.add_field(name="/temp_voice password {voice_channel} {password}", value="""**`如果目標語音頻道是臨時語音系統建立的並且有上鎖就可以用這個指令`**
                                                                                                            > 在第一個變數內選擇你要解鎖的語音頻道
                                                                                                            > 第二個變數輸入那個語音擁有者所設定的密碼""", inline=False)
        await interaction.response.send_message(embed=help_embed)

    @app_commands.command(name="create", description="建立臨時語音通道")
    @app_commands.describe(
        voice_channel="設定臨時語音的語音頻道",
        text_channel="設定臨時語音面板位置"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create(self, interaction: discord.Interaction, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel):
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

    @app_commands.command(name="password", description="輸入解鎖臨時語音的密碼")
    @app_commands.describe(
        voice_channel="要加入的語音頻道",
        password="頻道密碼"
    )
    async def enter_password(self, interaction: discord.Interaction, voice_channel: discord.VoiceChannel, password: str):
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

    @app_commands.command(name="remove", description="移除臨時語音通道")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete(self, interaction: discord.Interaction):
        guild = interaction.guild
        file_path = f'temp_voice/{guild.id}.json'
        
        if os.path.exists(file_path):
            os.remove(file_path)
            await interaction.response.send_message("臨時語音系統設置已被移除。請注意，相關的頻道和分類並未被刪除。", ephemeral=True)
        else:
            await interaction.response.send_message("此伺服器沒有臨時語音系統的設置文件。", ephemeral=True)

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
        
        # Restore original permissions for the channel owner
        await self.voice_channel.set_permissions(interaction.user, 
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
        
        with open(file_path, 'w') as f:
            json.dump(data, f)

async def on_voice_state_update(member, before, after):
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

async def setup(bot):
    cog = TemporaryVoice(bot)
    await bot.add_cog(cog)
    bot.add_listener(on_voice_state_update)

