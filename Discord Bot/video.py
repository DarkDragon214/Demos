import discord
import os
import random
import string
import requests
import html5lib
import asyncio
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from itertools import cycle
from apiclient.discovery import build

class Video(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def yt(self, ctx, *, terms=''):
        if terms == '':
            await ctx.send('```.yt (message)```')

        search_url = 'https://www.googleapis.com/youtube/v3/search'
        video_url = 'https://www.googleapis.com/youtube/v3/videos'
        ytURL = 'https://www.youtube.com/watch?v='

        search_params = {
            'key' : GoogleAPI,
            'q' : terms,
            'part' : 'snippet',
            'maxResults' : 9,
            'type' : 'video'
            }
        
        try: r = requests.get(search_url, params=search_params)
        except: await ctx.send('Request throttled due to daily limit being reached. Try again tomorrow loser.')    
        
        results = r.json()['items']
        vID = []

        for result in results:
            vID.append(result['id']['videoId'])
            
        video_params = {
            'key' : GoogleAPI,
            'id' : ','.join(vID),
            'part' : 'snippet,contentDetails',
            'maxResults' : 9
            }
        
        r = requests.get(video_url, params=video_params)
        results = r.json()['items']
        videos = []
        
        for result in results:
            video_data = {
                'id' : result['id'],
                'url' : f'https://www.youtube.com/watch?v={ result["id"] }',
                'publishedAt' : result['snippet']['publishedAt'],
                'title' : result['snippet']['title'],
                'description' : result['snippet']['description']
                }
            videos.append(video_data)
        vidLink = []
        vidTitle = []
        vidDesc = []
        vidPubl = []
        finalVL = []
        finalT = []
        finalD = []
        finalP = []
        for item in videos:
            vidLink = item['url']
            vidTitle = item['title']
            vidDesc = item['description']
            vidPubl = item['publishedAt']
            finalVL.append(vidLink)
            finalT.append(vidTitle)
            finalD.append(vidDesc)
            finalP.append(vidPubl)
        
        pos = 0
        embed = discord.Embed(title = None, description = '**Video Search Results**', colour = discord.Colour.blue())
        embed.set_footer(text='Video not here? Try using a more specific search.')
        
        for shit in finalT:
            embed.add_field(name= pos+1, value= finalT[pos])
            pos = pos+1
            
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        channel = ctx.channel
        message = await ctx.send(embed=embed)
        
        def check(m):
            return ctx.author == m.author and ( m.content == '1' or m.content == '2' or m.content == '3' or m.content == '4' or m.content == '5' or m.content == '6' or m.content == '7' or m.content == '8' or m.content == '9')

        msg = await self.client.wait_for('message', check=check)
        msgF = int(msg.content)-1
        xdd = finalVL[msgF]
        desc = finalD[msgF]
        Fdesc = desc.replace('\n',' | | ').replace('\r',' | | ')
        Fdesc = Fdesc[:200]
        publ = finalP[msgF]
        Fpubl = publ[:10]
        finalXDD = ''+xdd+'\n**'+finalT[msgF]+'**\n'+'`'+Fpubl+' - '+Fdesc+'...`'
        await message.edit(content=finalXDD, embed=None)

def setup(client):
    client.add_cog(Video(client))
    
YoutubeAPI = ''
SearchID = '1023984102834:faketoken'
GoogleAPI = 'asSDfnlSna109234exampletoken'