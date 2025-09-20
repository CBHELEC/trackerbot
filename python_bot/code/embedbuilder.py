import io
import re
import copy
import json
import datetime
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

class InputModal(discord.ui.Modal):
  def __init__(self, name, *text_inputs):
    super().__init__(title = '{} Modal'.format(name), timeout = 300.0)
    for text_input in text_inputs:
      self.add_item(text_input)
  
  async def on_submit(self, interaction):
    self.interaction = interaction # to access modal's interaction

class ImportView(discord.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    self.return_to = None
    self.return_callback = None # the function to run after getting json data from any of the 3 ways
    self.has_message_button = True
  
  @discord.ui.button(label = 'Import JSON with Modal', style = discord.ButtonStyle.green)
  async def modal_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = 'JSON Data', 
      placeholder = 'Paste JSON data here.',
      style = discord.TextStyle.long
    )
    
    modal = InputModal('Import JSON', text_input)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    try:
      data = json.loads(text_input.value)
    except Exception as error:
      error.interaction = modal.interaction
      raise error
    await self.return_callback(modal.interaction, data)
  
  @discord.ui.button(label = 'Import JSON with MystBin', style = discord.ButtonStyle.green)
  async def mystbin_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = 'MystBin Link', 
      placeholder = 'e.g. https://mystb.in/QuickBrownFox'
    )
    
    modal = InputModal('Import MystBin', text_input)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    try:
      value = text_input.value
      pattern = r'^https:\/\/mystb\.in\/[A-z]*'
      assert re.match(pattern, value), 'Invalid MystBin link.'
      paste_id = value.split('/')[-1]

      url = 'https://api.mystb.in/paste/{}'.format(paste_id) # can be improved, see BaseView.export_data()
      async with self.base_view.session.get(url) as resp:
        assert resp.status == 200, 'Failed to fetch paste from MystBin.'
        json_data = await resp.json(content_type = None)
        data = json.loads(json_data['files'][0]['content']) # ['content'] is a str
        
    except Exception as error:
      error.interaction = modal.interaction
      raise error

    await self.return_callback(modal.interaction, data)
    
  @discord.ui.button(label = 'Import from Message URL', style = discord.ButtonStyle.green)
  async def message_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = 'Message URL/Link', 
      placeholder = 'e.g. https://discord.com/channels/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX'
    )
    
    modal = InputModal('Import Message', text_input)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    try:
      value = text_input.value.split('/')[-3:]
  
      if interaction.guild:
        guild_id, channel_id, message_id = map(int, value)
        assert interaction.guild.id == guild_id, 'Message is not in the same guild.'
  
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
          channel = await interaction.guild.fetch_channel(channel_id)
          
        message = await channel.fetch_message(message_id)
      else:
        message_id = int(value[-1])
        message = await interaction.user.fetch_message(message_id)
        
      data = {}
      if message.content:
        data['content'] = message.content
      if message.embeds:
        data['embeds'] = [ # to be consistent with modal and mystbin input
          embed.to_dict() # embeds need to be as json
          for embed in message.embeds
        ]
      
    except Exception as error:
      error.interaction = modal.interaction
      raise error
      
    await self.return_callback(modal.interaction, data)
    
  @discord.ui.button(label = 'Back', style = discord.ButtonStyle.blurple)
  async def back_button(self, interaction, button):
    self.base_view.set_items(self.return_to)
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Stop', style = discord.ButtonStyle.red)
  async def stop_button(self, interaction, button):
    await self.base_view.on_timeout(interaction)

class SelectView(discord.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    self.options_list = [] # list of options in chunks of 25
    self.has_page_buttons = True
    self.page_index = 0
    self.return_to = None # controls where back button goes, set later

  def update_options(self, options):
    n = 25 # max options in a select
    if len(options) > n:
      if not self.has_page_buttons:
        self.add_item(self.left_button)
        self.add_item(self.what_button)
        self.add_item(self.right_button)
        self.has_page_buttons = True

        self.remove_item(self.back_button)
        self.remove_item(self.stop_button)
        self.add_item(self.back_button)
        self.add_item(self.stop_button)
        
      self.options_list = [options[i:i+n] for i in range(0, len(options), n)]
      self.dynamic_select.options = self.options_list[0]
      self.page_index = 0
      
      self.left_button.disabled = True
      self.right_button.disabled = False
      self.what_button.label = 'Page 1/{}'.format(len(self.options_list))
  
    else:
      if self.has_page_buttons:
        self.remove_item(self.left_button)
        self.remove_item(self.what_button)
        self.remove_item(self.right_button)
        self.has_page_buttons = False
      self.dynamic_select.options = options
        
  @discord.ui.select(options = [discord.SelectOption(label = ' ')])
  async def dynamic_select(self, interaction, select):
    pass # callback is changed often

  @discord.ui.button(label = '<')
  async def left_button(self, interaction, button):
    self.page_index -= 1
    if self.page_index == 0:
      button.disabled = True
    self.right_button.disabled = False
    self.what_button.label = 'Page {}/{}'.format(self.page_index+1, len(self.options_list))
    self.dynamic_select.options = self.options_list[self.page_index]
    await interaction.response.edit_message(view = self.base_view)
    
  @discord.ui.button(label = 'Page X/Y', disabled = True)
  async def what_button(self, interaction, button):
    pass # purely to tell what button page it is
    
  @discord.ui.button(label = '>')
  async def right_button(self, interaction, button):
    self.page_index += 1
    if self.page_index == len(self.options_list)-1:
      button.disabled = True
    self.left_button.disabled = False
    self.what_button.label = 'Page {}/{}'.format(self.page_index+1, len(self.options_list))
    self.dynamic_select.options = self.options_list[self.page_index]
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Back', style = discord.ButtonStyle.blurple)
  async def back_button(self, interaction, button):
    self.base_view.set_items(self.return_to)
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Stop', style = discord.ButtonStyle.red)
  async def stop_button(self, interaction, button):
    await self.base_view.on_timeout(interaction)

class SendView(discord.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    if not self.base_view.interaction.guild:
      self.channel_button.disabled = True

  @discord.ui.button(label = 'Send to Channel', style = discord.ButtonStyle.green)
  async def channel_button(self, interaction, button):
    placeholder = 'Select the Channel to send to...'
    guild = interaction.guild
    options = [
      discord.SelectOption(
        label = '#{}'.format(channel.name[:99]),
        description = '{} - {}'.format(
          channel.id,
          channel.topic[:75] if channel.topic else '(no description)'
        ),
        value = channel.id
      )
      for channel in sorted(guild.channels, key = lambda x: x.position)
      if isinstance(channel, discord.TextChannel) # text channels only
      if channel.permissions_for(interaction.user).send_messages # anti-abuse, user needs send msg perms
    ]
    async def callback(interaction):
      channel_id = int(self.base_view.get_select_value())
      
      try:
        channel = guild.get_channel(channel_id)
        if not channel:
          channel = await guild.fetch_channel(channel_id)
        await channel.send(content = self.base_view.content, embeds = self.base_view.embeds)
        
      except Exception as error:
        error.interaction = interaction
        raise error

      await interaction.response.send_message(
        content = 'Sent message to {}!'.format(channel.mention),
        ephemeral = True
      )
      
    self.base_view.set_select(placeholder, options, callback, 'send')
    self.base_view.set_items('select')
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Send to Webhook', style = discord.ButtonStyle.green)
  async def webhook_button(self, interaction, button):    
    text_input = discord.ui.TextInput(
      label = 'Webhook URL', 
      placeholder = 'e.g. https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    )
    
    modal = InputModal(button.label, text_input)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    webhook_url = text_input.value
    try:
      webhook = discord.Webhook.from_url(webhook_url, session = self.base_view.session)
      await webhook.send(content = self.base_view.content, embeds = self.base_view.embeds)
    except Exception as error:
      error.interaction = modal.interaction
      raise error
      
    await modal.interaction.response.send_message(
      content = 'Sent message to a Webhook!',
      ephemeral = True
    )

  @discord.ui.button(label = 'Edit Message URL', style = discord.ButtonStyle.green, )
  async def message_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = 'Message URL/Link', 
      placeholder = 'e.g. https://discord.com/channels/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX',
    )
    
    modal = InputModal(button.label, text_input)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    try:
      data = text_input.value.split('/')[-3:]
  
      if interaction.guild:
        guild_id, channel_id, message_id = map(int, data)
        assert interaction.guild.id == guild_id, 'Message is not in the same guild.'
  
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
          channel = await interaction.guild.fetch_channel(channel_id)
        
        assert channel.permissions_for(interaction.user).send_messages, 'You need send_messages permission in the message channel.'

        message = await channel.fetch_message(message_id)
        
        if not channel.permissions_for(interaction.user).administrator:
          # this is a tiny anti-abuse measure
          # e.g. you dont want non-admins to edit a message sent months ago, it would be hard to find
          # you could add some log system to track edits, or just disable this button completely for non-admins
          now = datetime.datetime.now(datetime.timezone.utc)
          seconds_elapsed = (now - message.created_at).seconds
          assert seconds_elapsed < 300, 'Non-admins are disallowed from editing messages older than 5 minutes.'
          
        where = channel.mention
      else:
        message_id = int(data[-1])
        message = await interaction.user.fetch_message(message_id)
        where = 'our DMs'
        
      await message.edit(content = self.base_view.content, embeds = self.base_view.embeds)
      
    except Exception as error:
      error.interaction = modal.interaction
      raise error
      
    await modal.interaction.response.send_message(
      content = 'Edited message `{}` in {}!'.format(message_id, where),
      ephemeral = True
    )

  @discord.ui.button(label = 'Back', style = discord.ButtonStyle.blurple)
  async def back_button(self, interaction, button):
    self.base_view.set_items('message')
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Stop', style = discord.ButtonStyle.red)
  async def stop_button(self, interaction, button):
    await self.base_view.on_timeout(interaction)
  
class EmbedView(discord.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    
    self.embed = None # the following are changed often
    self.embed_dict = None # used for default values and reverting changes
    self.embed_original = None # for resetting
    self.embed_index = None # index in self.embeds

  def update_fields(self, embed_dict = None): # ensures field-related buttons are disabled correctly
    embed_dict = embed_dict or self.embed_dict
    if 'fields' in embed_dict and embed_dict['fields']:
      self.remove_field_button.disabled = False
      self.clear_fields_button.disabled = False
      self.edit_field_button.disabled = False
      if len(embed_dict['fields']) == 25: # max fields in embed
        self.add_field_button.disabled = True
      else:
        self.add_field_button.disabled = False
    else:
      self.remove_field_button.disabled = True
      self.clear_fields_button.disabled = True
      self.edit_field_button.disabled = True
      self.add_field_button.disabled = False
    
  async def do(self, interaction, button, *text_inputs, method = None):
    name = button.label.lower()

    old_values = []
    for text_input in text_inputs:
      old = self.embed_dict.get(name, None)
      if hasattr(text_input, 'key'):
        if old:
          old = old.get(text_input.key, None)
      text_input.default = old
      old_values.append(old)
    
    modal = InputModal(button.label, *text_inputs)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    new_values = []
    for text_input in text_inputs:
      new = text_input.value.strip()
      if new:
        if hasattr(text_input, 'convert'):
          try:
            new = text_input.convert(new)
          except Exception as error:
            error.interaction = modal.interaction
            raise error
        new_values.append(new)
      else:
        new_values.append(None)

    if old_values == new_values: # embed is the same
      return await modal.interaction.response.defer()

    try:
      if method:
        kwargs = {
          text_input.key : new
          for text_input, new in zip(text_inputs, new_values)
        }
        getattr(self.embed, method)(**kwargs) # embed.set_author(name=...,url=...)
      else:
        setattr(self.embed, name, new_values[0]) # embed.title = ...
      await modal.interaction.response.edit_message(embeds = self.base_view.embeds)
      self.embed_dict = copy.deepcopy(self.embed.to_dict())
      
    except Exception as error:
      self.embed = discord.Embed.from_dict(self.embed_dict)
      self.base_view.embeds[self.embed_index] = self.embed
      raise error

  @discord.ui.button(label = ' ', disabled = True)
  async def what_button(self, interaction, button):
    pass # label is edited to say which embed you're editing

  @discord.ui.button(label = 'Title', style = discord.ButtonStyle.blurple)
  async def title_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'The title of the embed.', 
      required = False
    )
    await self.do(interaction, button, text_input)

  @discord.ui.button(label = 'URL', style = discord.ButtonStyle.blurple)
  async def url_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'The URL of the embed.', 
      required = False
    )
    await self.do(interaction, button, text_input)

  @discord.ui.button(label = 'Description', style = discord.ButtonStyle.blurple)
  async def description_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'The description of the embed.', 
      style = discord.TextStyle.long,
      required = False
    )
    await self.do(interaction, button, text_input)

  @discord.ui.button(label = 'Color', style = discord.ButtonStyle.blurple)
  async def color_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'A hex string like "#ffab12" or a number <= 16777215.', 
      required = False
    )
    text_input.convert = lambda x: int(x) if x.isnumeric() else int(x.lstrip('#'), base = 16)
    await self.do(interaction, button, text_input)

  @discord.ui.button(label = 'Timestamp', style = discord.ButtonStyle.blurple)
  async def timestamp_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'A unix timestamp or a number like "1659876635".', 
      required = False
    )
    def convert(x):
      try:
        return datetime.datetime.fromtimestamp(int(x))
      except:
        return datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S%z') # 1970-01-02T10:12:03+00:00
        
    text_input.convert = convert
    await self.do(interaction, button, text_input)

  @discord.ui.button(label = 'Author', style = discord.ButtonStyle.blurple)
  async def author_button(self, interaction, button):
    name_input = discord.ui.TextInput(
      label = 'Author Name', 
      placeholder = 'The name of the author.', 
      required = False
    )
    name_input.key = 'name'
    url_input = discord.ui.TextInput(
      label = 'Author URL', 
      placeholder = 'The URL for the author.', 
      required = False
    )
    url_input.key = 'url'
    icon_input = discord.ui.TextInput(
      label = 'Author Icon URL', 
      placeholder = 'The URL for the author icon.', 
      required = False
    )
    icon_input.key = 'icon_url'
    text_inputs = [name_input, url_input, icon_input]
    await self.do(interaction, button, *text_inputs, method = 'set_author')

  @discord.ui.button(label = 'Thumbnail', style = discord.ButtonStyle.blurple)
  async def thumbnail_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'The source URL for the thumbnail.', 
      required = False
    )
    text_input.key = 'url'
    await self.do(interaction, button, text_input, method = 'set_thumbnail')

  @discord.ui.button(label = 'Image', style = discord.ButtonStyle.blurple)
  async def image_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'The source URL for the image.', 
      required = False
    )
    text_input.key = 'url'
    await self.do(interaction, button, text_input, method = 'set_image')

  @discord.ui.button(label = 'Footer', style = discord.ButtonStyle.blurple)
  async def footer_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = 'Footer Text', 
      placeholder = 'The footer text.', 
      required = False
    )
    text_input.key = 'text'
    icon_input = discord.ui.TextInput(
      label = 'Footer Icon URL', 
      placeholder = 'The URL of the footer icon.', 
      required = False
    )
    icon_input.key = 'icon_url'
    text_inputs = [text_input, icon_input]
    await self.do(interaction, button, *text_inputs, method = 'set_footer')

  @discord.ui.button(label = 'Add Field', style = discord.ButtonStyle.blurple)
  async def add_field_button(self, interaction, button):
    name_input = discord.ui.TextInput(
      label = 'Field Name', 
      placeholder = 'The name of the field.'
    )
    value_input = discord.ui.TextInput(
      label = 'Field Value', 
      placeholder = 'The value of the field.',
      style = discord.TextStyle.long
    )
    inline_input = discord.ui.TextInput(
      label = 'Field Inline (Optional)', 
      placeholder = 'Type "1" for inline, otherwise not inline.',
      required = False
    )
    index_input = discord.ui.TextInput(
      label = 'Field Index (Optional)',
      placeholder = 'Insert before field(n+1), default at the end.',
      required = False
    )
    text_inputs = [name_input, value_input, inline_input, index_input]
    
    modal = InputModal(button.label, *text_inputs)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    inline = inline_input.value.strip() == '1'
    index = None
    if index_input.value.strip().isnumeric():
      index = int(index_input.value)
                     
    embed = discord.Embed.from_dict(copy.deepcopy(self.embed_dict))
    
    kwargs = {
      'name' : name_input.value,
      'value' : value_input.value,
      'inline' : inline
    }
    if index or index == 0:
      kwargs['index'] = index
      embed.insert_field_at(**kwargs)
    else:
      embed.add_field(**kwargs)

    self.update_fields(embed.to_dict())
    self.base_view.embeds[self.embed_index] = embed
    
    try:
      await modal.interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
    except Exception as error:
      self.update_fields()
      self.base_view.embeds[self.embed_index] = self.embed
      raise error

    self.embed = embed
    self.embed_dict = copy.deepcopy(embed.to_dict())

  @discord.ui.button(label = 'Edit Field', style = discord.ButtonStyle.blurple)
  async def edit_field_button(self, interaction, button):
    placeholder = 'Select the Field to edit...'
    options = [
      discord.SelectOption(
        label = 'Field {}'.format(i+1), 
        description = field['name'][:100],
        value = i
      )
      for i, field in enumerate(self.embed_dict['fields'])
    ]
    async def callback(interaction):
      index = int(self.base_view.get_select_value())
      field = self.embed_dict['fields'][index]
      name_input = discord.ui.TextInput(
        label = 'Field Name', 
        placeholder = 'The name of the field.',
        default = field['name']
      )
      value_input = discord.ui.TextInput(
        label = 'Field Value', 
        placeholder = 'The value of the field.',
        style = discord.TextStyle.long,
        default = field['value']
      )
      inline_input = discord.ui.TextInput(
        label = 'Field Inline (Optional)', 
        placeholder = 'Type "1" for inline, otherwise not inline.',
        required = False,
        default = str(int(field['inline']))
      )
      text_inputs = [name_input, value_input, inline_input]
      
      modal = InputModal(button.label, *text_inputs)
      await interaction.response.send_modal(modal)
      timed_out = await modal.wait()
      if timed_out:
        return

      inline = inline_input.value.strip() == '1'
                       
      kwargs = {
        'index' : index,
        'name' : name_input.value,
        'value' : value_input.value,
        'inline' : inline
      }
  
      embed = discord.Embed.from_dict(copy.deepcopy(self.embed_dict))
      embed.set_field_at(**kwargs)
  
      if embed == self.embed: # same field name, value
        return await modal.interaction.response.defer()
  
      self.update_fields(embed.to_dict())
      self.base_view.embeds[self.embed_index] = embed
      self.base_view.set_items('embed')
      
      try:
        await modal.interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
      except Exception as error:
        self.update_fields()
        self.base_view.embeds[self.embed_index] = self.embed
        self.base_view.set_items('select') 
        raise error
  
      self.embed = embed
      self.embed_dict = copy.deepcopy(embed.to_dict())

    self.base_view.set_select(placeholder, options, callback, 'embed')
    self.base_view.set_items('select')
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Remove Field', style = discord.ButtonStyle.blurple)
  async def remove_field_button(self, interaction, button):
    placeholder = 'Select the Field to remove...'
    options = [
      discord.SelectOption(
        label = 'Field {}'.format(i+1), 
        description = field['name'][:100],
        value = i
      )
      for i, field in enumerate(self.embed_dict['fields'])
    ]
    async def callback(interaction):
      index = int(self.base_view.get_select_value())
      self.embed.remove_field(index)
      self.embed_dict = copy.deepcopy(self.embed.to_dict())
      self.update_fields()
      self.base_view.set_items('embed')
      await interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)

    self.base_view.set_select(placeholder, options, callback, 'embed')
    self.base_view.set_items('select')
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Clear Fields', style = discord.ButtonStyle.red)
  async def clear_fields_button(self, interaction, button):
    self.embed.clear_fields()
    self.embed_dict = copy.deepcopy(self.embed.to_dict())
    self.update_fields()
    await interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)

  @discord.ui.button(label = 'Reset', style = discord.ButtonStyle.red)
  async def reset_button(self, interaction, button):
    self.embed = discord.Embed.from_dict(copy.deepcopy(self.embed_original))
    self.base_view.embeds[self.embed_index] = self.embed
    self.embed_dict = copy.deepcopy(self.embed_original)
    self.update_fields()
    await interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)

  @discord.ui.button(label = 'Import JSON [2]', style = discord.ButtonStyle.green)
  async def import_button(self, interaction, button):    
    async def return_callback(interaction, data):
      try:
        self.embed = discord.Embed.from_dict(data)
      except Exception as error:
        error.interaction = interaction
        raise error

      self.embed_dict = copy.deepcopy(data)
      self.base_view.embeds[self.embed_index] = self.embed

      self.update_fields()
      self.base_view.set_items('embed')
      await interaction.response.edit_message(
        content = self.base_view.content,
        embeds = self.base_view.embeds,
        view = self.base_view
      )
      
    self.base_view.set_import(return_callback, 'embed')
    self.base_view.set_items('import')
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Export JSON', style = discord.ButtonStyle.green)
  async def export_button(self, interaction, button):
    await self.base_view.export_data(interaction, self.embed_dict)
  
  @discord.ui.button(label = 'Back', style = discord.ButtonStyle.blurple)
  async def back_button(self, interaction, button):
    self.base_view.set_items('message')
    await interaction.response.edit_message(view = self.base_view)

  @discord.ui.button(label = 'Stop', style = discord.ButtonStyle.red)
  async def stop_button(self, interaction, button):
    await self.base_view.on_timeout(interaction)

class MessageView(discord.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
  
  def update_embeds(self): # ensures embed-related buttons are disabled correctly
    if self.base_view.embeds:
      self.edit_embed_button.disabled = False
      self.remove_embed_button.disabled = False
      self.clear_embeds_button.disabled = False
      if len(self.base_view.embeds) == 10: # max embeds in a message
        self.add_embed_button.disabled = True
      else:
        self.add_embed_button.disabled = False
    else:
      self.edit_embed_button.disabled = True
      self.remove_embed_button.disabled = True
      self.clear_embeds_button.disabled = True
      self.add_embed_button.disabled = False
  
  @discord.ui.button(label = 'Content', style = discord.ButtonStyle.blurple)
  async def content_button(self, interaction, button):
    text_input = discord.ui.TextInput(
      label = button.label, 
      placeholder = 'The actual contents of the message.',
      style = discord.TextStyle.long,
      default = self.base_view.content,
      required = False
    )
    
    modal = InputModal(button.label, text_input)
    await interaction.response.send_modal(modal)
    timed_out = await modal.wait()
    if timed_out:
      return

    content = text_input.value
    await modal.interaction.response.edit_message(content = content)
    self.base_view.content = content

  @discord.ui.button(label = 'Add Embed', style = discord.ButtonStyle.blurple)
  async def add_embed_button(self, interaction, button):
    embed = discord.Embed(title = 'New embed {}'.format(len(self.base_view.embeds)+1))
    self.base_view.embeds.append(embed)
    self.update_embeds()
    try:
      await interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
    except ValueError as error:
      error.interaction = interaction
      self.base_view.embeds.pop()
      self.update_embeds()
      raise error

  @discord.ui.button(label = 'Edit Embed', style = discord.ButtonStyle.blurple, disabled = True)
  async def edit_embed_button(self, interaction, button):
    placeholder = 'Select the Embed to edit...'
    options = [
      discord.SelectOption(
        label = 'Embed {}'.format(i+1),
        description = (
          self.base_view.embeds[i].title[:100] 
          if self.base_view.embeds[i].title
          else '(no title)'
        ),
        value = i
      )
      for i in range(len(self.base_view.embeds))
    ]
    async def callback(interaction):
      index = int(self.base_view.get_select_value())
      self.base_view.set_embed(index)
      self.base_view.set_items('embed')
      await interaction.response.edit_message(view = self.base_view)
      
    self.base_view.set_select(placeholder, options, callback)
    self.base_view.set_items('select')
    await interaction.response.edit_message(view = self.base_view)
    
  @discord.ui.button(label = 'Remove Embed', style = discord.ButtonStyle.blurple, disabled = True)
  async def remove_embed_button(self, interaction, button):
    placeholder = 'Select the Embed to remove...'
    options = [
      discord.SelectOption(
        label = 'Embed {}'.format(i+1),
        description = (
          self.base_view.embeds[i].title[:100] 
          if self.base_view.embeds[i].title
          else '(no title)'
        ),
        value = i
      )
      for i in range(len(self.base_view.embeds))
    ]
    async def callback(interaction):
      index = int(self.base_view.get_select_value())
      self.base_view.embeds.pop(index)
      self.update_embeds()
      self.base_view.set_items('message')
      await interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
      
    self.base_view.set_select(placeholder, options, callback)
    self.base_view.set_items('select')
    await interaction.response.edit_message(view = self.base_view)
    
  @discord.ui.button(label = 'Clear Embeds', style = discord.ButtonStyle.red, disabled = True)
  async def clear_embeds_button(self, interaction, button):
    self.base_view.embeds = []
    self.update_embeds()
    await interaction.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)

  @discord.ui.button(label = 'Reset', style = discord.ButtonStyle.red)
  async def reset_button(self, interaction, button):
    self.base_view.content = self.base_view.original_content
    self.base_view.embeds = []
    self.update_embeds()
    await interaction.response.edit_message(
      content = self.base_view.content, 
      embeds = self.base_view.embeds, 
      view = self.base_view
    )

  @discord.ui.button(label = 'Import JSON [3]', style = discord.ButtonStyle.green)
  async def import_button(self, interaction, button):
    async def return_callback(interaction, data):
      if 'content' in data and data['content']:
        self.base_view.content = data['content']
      else:
        self.base_view.content = None

      if 'embeds' in data and data['embeds']: # convert embeds from json to objects
        self.base_view.embeds = [
          discord.Embed.from_dict(embed)
          for embed in data['embeds']
        ]
      else:
        self.base_view.embeds = []
        
      self.update_embeds()
      self.base_view.set_items('message')
      await interaction.response.edit_message(
        content = self.base_view.content,
        embeds = self.base_view.embeds,
        view = self.base_view
      )

    self.base_view.set_import(return_callback, 'message')
    self.base_view.set_items('import')
    await interaction.response.edit_message(view = self.base_view)
    
  @discord.ui.button(label = 'Export JSON', style = discord.ButtonStyle.green)
  async def export_button(self, interaction, button):
    data = {}
    
    if self.base_view.content:
      data['content'] = self.base_view.content
    if self.base_view.embeds:
      data['embeds'] = [
        embed.to_dict()
        for embed in self.base_view.embeds
      ]

    await self.base_view.export_data(interaction, data)

  @discord.ui.button(label = 'Send [3]', style = discord.ButtonStyle.green)
  async def send_button(self, interaction, button):
    self.base_view.set_items('send')
    await interaction.response.edit_message(view = self.base_view)
  
  @discord.ui.button(label = 'Stop', style = discord.ButtonStyle.red)
  async def stop_button(self, interaction, button):
    await self.base_view.on_timeout(interaction)

class BaseView(discord.ui.View):
  def __init__(self, interaction, session):
    super().__init__()
    self.interaction = interaction
    self.session = session
    self.message = None # set later, used for timeout edits
    self.content = 'Message Maker!'
    self.original_content = self.content
    self.embeds = []
    self.views = {
      'message' : MessageView(self),
      'embed' : EmbedView(self),
      'select' : SelectView(self),
      'import' : ImportView(self),
      'send' : SendView(self)
    }
    self.set_items('message')

  def set_message(self, message):
    self.message = message
  
  def set_items(self, key):
    self.clear_items()
    for item in self.views[key].children:
      self.add_item(item)

  def set_select(self, placeholder, options, callback, return_to = None):
    view = self.views['select']
    view.return_to = return_to or 'message'
    select = view.dynamic_select
    select.placeholder = placeholder
    select.callback = callback
    view.update_options(options)

  def set_embed(self, index):
    embed = self.embeds[index]
    view = self.views['embed']
    view.embed = embed
    view.embed_dict = copy.deepcopy(embed.to_dict())
    view.embed_original = discord.Embed(title = 'New embed {}'.format(index+1)).to_dict()
    view.embed_index = index
    view.what_button.label = '*Editing Embed {}'.format(index+1)
    view.update_fields()

  def set_import(self, return_callback, return_to):
    view = self.views['import']
    view.return_callback = return_callback
    view.return_to = return_to
    before = view.has_message_button
    if return_to == 'message': # hide import from message button if its not message json
      if not view.has_message_button:
        view.add_item(view.message_button)
        view.has_message_button = True
        view.remove_item(view.back_button) # move back and stop button position ahead of message button
        view.remove_item(view.stop_button)
        view.add_item(view.back_button)
        view.add_item(view.stop_button)
    else:
      if view.has_message_button:
        view.remove_item(view.message_button)
        view.has_message_button = False
      
  def get_select_value(self):
    select = self.views['select'].dynamic_select
    return select.values[0]

  async def export_data(self, interaction, data : dict):
    if data:
      text = json.dumps(data, indent = 2)
    else:
      text = '(no data)'
      
    frame = '```json\n{}```'
  
    if len(text) > 2000 - len(frame) - 2:
      # this can be improved e.g. handle ratelimits, cooldowns, errors
      # or use https://pypi.org/project/mystbin-py/
      filename = 'messagemaker.json'
      payload = {'files' : [{'content' : text, 'filename' : filename}]}
      paste_url = None
      async with self.session.put('https://api.mystb.in/paste', json = payload) as resp:
        if resp.status == 201:
          paste_url = 'https://mystb.in/{}'.format((await resp.json(content_type = None))['id'])
      if paste_url:
        content = 'Uploaded to: {}'.format(paste_url)
      else:
        content = 'Failed to upload to MystBin.'
      file = discord.File(io.StringIO(text), filename = filename)
      await interaction.response.send_message(content, file = file, ephemeral = True)
    else:
      await interaction.response.send_message(frame.format(text), ephemeral = True)
    
  async def interaction_check(self, interaction):
    if interaction.user == self.interaction.user:
      return True
    await interaction.response.send_message('This is not your interaction.', ephemeral = True)
    return False
    
  async def on_timeout(self, interaction = None):
    try: # hide buttons
      if interaction: # clicked stop
        self.stop()
        await interaction.response.edit_message(view = None) 
      else:
        await self.message.edit(view = None) # timed out
    except discord.HTTPException: # disable buttons if message is empty
      for item in self.children:
        item.disabled = True
      await self.message.edit(view = self)
    
  async def on_error(self, interaction, error, item):
    embed = discord.Embed(
      title = 'Edit failed',
      description = '```fix\n{}```',
      color = discord.Color.red()
    )
    if isinstance(error, discord.HTTPException):
      embed.description = embed.description.format(error.text)
    elif isinstance(error, (ValueError, TypeError, AssertionError)):
      embed.description = embed.description.format(str(error))
    else:
      # print('unhandled error:', interaction, error, item, error.__class__.__mro__, sep = '\n')
      raise error
    embed.description = embed.description or 'No reason provided.'
    if hasattr(error, 'interaction'): # use interaction if available e.g. .convert() failed
      await error.interaction.response.send_message(embed = embed, ephemeral = True)
    else: # otherwise followup e.g. for max embeds reached
      await self.interaction.followup.send(embed = embed, ephemeral = True)