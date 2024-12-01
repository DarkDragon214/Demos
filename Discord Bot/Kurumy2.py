import discord
import os
import random
import requests
import html5lib
import string
import asyncio
import interactions
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from itertools import cycle
from apiclient.discovery import build

bot = interactions.Client(token='exampletoken')

@bot.command(name="name",
             description="Displays your name",
             options=[
                interactions.Option(
                    name="user",
                    description="target",
                    type=interactions.OptionType.STRING,
                    required=True)])
async def name(ctx: interactions.CommandContext, text: str):
    await ctx.send(str(user.name))

@bot.command(name="avatar",
             description="Displays your avatar",
             options=[
                interactions.Option(
                    name="user",
                    description="target",
                    type=interactions.OptionType.STRING,
                    required=True)])
async def avatar(ctx: interactions.CommandContext, *, user : discord.Member):
        await ctx.send(ctx.author.avatar_url)

@bot.command(name="img",
             description="Searches for an image",
             options=[
                interactions.Option(
                    name="terms",
                    description="Query for search",
                    type=interactions.OptionType.STRING,
                    required=True)])
async def img(ctx: interactions.CommandContext, *, terms=str):
        pg = 0
        maxResults = 10
        resource = build("customsearch", 'v1', developerKey=GoogleAPI).cse()
        images = []
        try :
            for i in range(1, maxResults, 10):
                result = resource.list(q=terms, cx=SearchID, searchType='image', start=i).execute()
                images += result['items']                 
        except: await ctx.send('Request throttled due to daily limit being reached. Try again tomorrow loser.')
        Search = result['items']
        final = []
        
        for item in images:
            image = item['link']
            final.append(image)
            url = final[pg]
        page = str(pg+1)
        MR = str(maxResults)
        foot = str('Page '+page+'/'+MR+'')
        embed = interactions.Embed(description = '**Image Search Results**', color = 0)
        embed.set_footer(text=foot)
        embed.set_image(url=url)
        await ctx.send(embeds=embed)
            
YoutubeAPI = ''
SearchID = '1023984102834:faketoken'
GoogleAPI = 'asSDfnlSna109234exampletoken'

bot.start()

