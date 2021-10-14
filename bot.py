import discord
from discord.ext import commands
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
from discord.utils import get
from config import settings
import random
from asyncio import sleep
import sqlite3 as sq
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timedelta, datetime

intents = discord.Intents.all() #получам права
bot = commands.Bot(command_prefix = settings['prefix'], intents = intents) #прогружаем префикс

with sq.connect('DataBase.db') as con:
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS warn (

        warn_id INTEGER PRIMARY KEY,
        warn_date TEXT NOT NULL,
        date_out TEXT NOT NULL,
        guild INT NOT NULL,
        user INT NOT NULL,
        reason TEXT NOT NULL,
        active BOOL DEFAULT TRUE

        )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS giverole (

    	"id" INTEGER PRIMARY KEY,
    	"guild_id"	INTEGER,
    	"role_id"	INTEGER,
    	"who_give"	INTEGER,
		"have"	INTEGER

        )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS whogivewarn (
    	"id_who_give"	INTEGER,
    	"guild_id"	INTEGER
        )""")

    con.commit()

@bot.event
async def on_ready():
          await bot.change_presence(status=discord.Status.online, activity=discord.Game("Разработчик Kira#6666"))

@bot.remove_command('help') #удаляем команду help

@bot.command()
async def help(ctx): # Создаём функцию и передаём аргумент ctx.
	member = ctx.message.author
	print(f"{datetime.now()} {member} вызвал help") #ПРИНТЫ
	embed = discord.Embed(colour=discord.Colour(0x417505))

	embed.set_footer(text="👁️ - адмниские или закрытые команды")
	embed.add_field(name="giverole (user) (role)", value="Позволяет выдать роль")
	embed.add_field(name="removerole", value="Позволяет снять роль")
	embed.add_field(name="flip", value="Подбросить монетку")
	embed.add_field(name="warnadd (user) (reason)", value="Выдать варн")
	embed.add_field(name="warnremove (warn id)", value="Снять варн")
	embed.add_field(name="warnlist (user)", value="Посмотреть все варны пользователя")
	embed.add_field(name="👁️ setting", value="Показывает настройки выдачи роли и варнов")
	embed.add_field(name="👁️ say (текст)", value="Отправить текст от имени бота")
	embed.add_field(name="👁️ sayto (канал; текст)", value="Отправить текст от имени бота в определенный канал")
	embed.add_field(name="👁️ allowgiverole (role которая будет выдавать роль) (role для выдачи) (0 или 1)", value="Разрешить выдачу ролей\n 0 - можно не иметь роль для её выдачи \n 1 - требуется иметь роль для её выдачи)")
	embed.add_field(name="👁️ delgiverole  (role которая выдает роль) (role для выдачи)", value="Забирает возможноть выдавать роли")
	embed.add_field(name="👁️ allowgivewarn (role) ", value="Разрешить выдачу варна этой роли")
	embed.add_field(name="👁️ delgivewarn (role) ", value="Запретить выдачу варна этой роли")
	await ctx.channel.send(embed=embed)

@bot.command()
async def setting(ctx):
	print(f"{datetime.now()} {ctx.message.author} вызвал setting") #ПРИНТЫ
	cur.execute(f"SELECT role_id, who_give, have FROM giverole WHERE guild_id = {ctx.guild.id}")
	record = cur.fetchall()
	embed = discord.Embed(title = f"Выдача ролей:", colour=discord.Colour(0x417505))
	for i in record:
	    role_id = discord.utils.get(ctx.guild.roles, id = int(f'{i[0]}'))
	    if role_id == None:
	    	role_id = f"Удаленная роль ID: {i[0]}"
	    role_whogive = discord.utils.get(ctx.guild.roles, id = int(f'{i[1]}'))
	    if role_whogive == None:
	    	role_whogive = f"Удаленная роль ID: {i[1]}"
	    role_have = int(f'{i[2]}')
	    if role_have == 0:
	        active = "❌"
	    else:
	        active = "✅"
	    embed.add_field(name=f"Роль: *{role_whogive}*", value=f" **Может выдать:** {role_id}\n**Проверка на наличие:** {active} ", inline=False)
	await ctx.channel.send(embed=embed)

	cur.execute(f"SELECT id_who_give FROM whogivewarn WHERE guild_id = {ctx.guild.id}")
	record = cur.fetchall()
	embed = discord.Embed(title = f"Выдача варнов:", colour=discord.Colour(0x417505))
	for i in record:
	    role_id = discord.utils.get(ctx.guild.roles, id = int(f'{i[0]}'))
	    if role_id == None:
	    	role_id = f"Удаленная роль ID: {i[0]}"
	    embed.add_field(name=f"Роль:", value=f"{role_id}", inline=False)
	await ctx.channel.send(embed=embed)

@bot.command()
async def giverole(ctx, opponent: discord.Member, squad_name: discord.Role):
	print(f"{datetime.now()} {ctx.message.author} пытается выдать роль {squad_name} для {opponent}") #ПРИНТЫ
	cur.execute(f"SELECT role_id, who_give, have FROM giverole WHERE role_id = {squad_name.id} AND guild_id = {ctx.guild.id}")
	record = cur.fetchall()
	if len(record) == 0:
		await ctx.send("Для этой роли - не были заданы разрешения выдачи")
	role_id = int(f'{record[0][0]}')
	role_whogive = discord.utils.get(ctx.guild.roles, id = int(f'{record[0][1]}'))
	role_have = int(f'{record[0][2]}')
	role = discord.utils.get(ctx.guild.roles, id=role_id)

	if role_whogive not in ctx.message.author.roles: 
		await ctx.send("Вы не можете выдавать данную роль")
		return
	if role_have == 1 and role not in ctx.message.author.roles:
		await ctx.send("Что бы выдать эту роль, вам необходимо иметь её")
		return

	await opponent.add_roles(role)
	await ctx.send(f"Вы выдали роль {role} {opponent}")



@bot.command()
async def removerole(ctx, opponent: discord.Member, squad_name: discord.Role):
	print(f"{datetime.now()} {ctx.message.author} пытается забрать роль {squad_name} у {opponent}") #ПРИНТЫ
	cur.execute(f"SELECT role_id, who_give, have FROM giverole WHERE role_id = {squad_name.id} AND guild_id = {ctx.guild.id}")
	record = cur.fetchall()
	if len(record) == 0:
		await ctx.send("Для этой роли - не были заданы разрешения выдачи")

	role_id = int(f'{record[0][0]}')
	role_whogive = discord.utils.get(ctx.guild.roles, id = int(f'{record[0][1]}'))
	role_have = int(f'{record[0][2]}')
	role = discord.utils.get(ctx.guild.roles, id=role_id)

	if role_whogive not in ctx.message.author.roles: 
		await ctx.send("Вы не можете забирать данную роль")
		return

	if role_have == 1 and role not in ctx.message.author.roles:
		await ctx.send("Что бы забрать эту роль, вам необходимо иметь её")
		return

	await opponent.remove_roles(role)
	await ctx.send(f"Вы забрали роль {role} у {opponent}")


@bot.command()
@has_permissions(administrator = True)
async def say(ctx, *, text):
	await ctx.message.delete()
	await ctx.send(text)


@bot.command()
@has_permissions(administrator = True)
async def sayto(ctx, channel:discord.TextChannel, *, text):
    await ctx.message.delete()
    await channel.send(text)


@bot.command()
async def flip(ctx):
    print(ctx.message.author, "flip")
    variable = [
        "Выпал: орел",
        "Выпала: решка",]
    await ctx.send("Вы подбросили монетку")
    await ctx.send(random.choice(variable))


@bot.command()
async def warnadd(ctx, opponent: discord.Member, warnreason: str):
	member = ctx.message.author
	print(f"{datetime.now()} {member} вызвал warnadd") #ПРИНТЫ
	cur.execute(f"SELECT id_who_give FROM whogivewarn WHERE guild_id = {ctx.guild.id}")
	record = cur.fetchall()
	if len(record) == 0:
		await ctx.send("У вас нету прав, для выдачи варнов")
		return
	warn_date = datetime.now().date()
	date_end = warn_date + timedelta(+7)
	cur.execute(f"INSERT INTO warn (warn_date, date_out, guild, user, reason) VALUES('{warn_date}', '{date_end}', {ctx.guild.id}, {opponent.id}, '{warnreason}')")
	con.commit()
	print(record)


@bot.command()
async def warnlist(ctx, opponent: discord.Member):
    searchuser = opponent.id
    guild = ctx.guild.id
    cur.execute(f"SELECT * FROM warn user WHERE(user = {searchuser} AND guild = {guild})")
    record = cur.fetchall()
    if len(record) == 0:
        await ctx.send(f"У данного пользователя нету варнов")
        return
    embed = discord.Embed(title = f"Варны {opponent}", colour=discord.Colour(0x417505))
    for i in record:
        idwarn = i[0]
        date = i[1]
        reason = i[5]
        active = i[6]
        if active == 1:
            active = "Активный"
        else:
            active = "Неактивный"
        embed.add_field(name=f"ID {idwarn} - {active}", value=f"Дата выдачи: {date} | Причина: {reason} ", inline=False)
    await ctx.channel.send(embed=embed)



@bot.command()
async def warnremove(ctx, warnid: str):
	cur.execute(f"SELECT id_who_give FROM whogivewarn WHERE guild_id = {ctx.guild.id}")
	record = cur.fetchall()
	if len(record) == 0:
		await ctx.send("У вас нету прав, для выдачи варнов")
		return
	cur.execute(f"UPDATE warn SET active = 0 WHERE warn_id = '{warnid}' AND active = 1")
	con.commit()
	if cur.rowcount < 1:
	    await ctx.send(f"Нет активного варна с ID: {warnid}")
	    return
	await ctx.send(f"Вы сняли варн с номером ID: {warnid}")
	

@bot.command()
@has_permissions(administrator = True)
async def allowgivewarn(ctx, role_id: discord.Role):
	cur.execute(f"INSERT INTO whogivewarn (guild_id, id_who_give) VALUES({ctx.guild.id}, {role_id.id})")
	con.commit()

@bot.command()
@has_permissions(administrator = True)
async def delgivewarn(ctx, role_id: discord.Role):
	cur.execute(f"UPDATE whogivewarn SET id_who_give = 0, guild_id = 0 WHERE id_who_give = {role_id.id}")
	con.commit()

@bot.command()
@has_permissions(administrator = True)
async def allowgiverole (ctx, who_give: discord.Role, role_id: discord.Role, have: int):
	if have != (0 or 1):
		await ctx.send(f"**Последний параметр - должен быть равен 0 или 1**\n 0 - можно не иметь роль для её выдачи \n 1 - требуется иметь роль для её выдачи")
		return
	cur.execute(f"INSERT INTO giverole (guild_id, role_id, who_give, have) VALUES({ctx.guild.id}, {role_id.id}, {who_give.id}, {have})")
	con.commit()

@bot.command()
@has_permissions(administrator = True)
async def delgiverole(ctx, who_give: discord.Role, role_id: discord.Role ):
	cur.execute(f"UPDATE giverole SET guild_id = 0 WHERE who_give = {who_give.id} AND role_id = {role_id.id}")
	con.commit()

async def func():
	mydate = datetime.now().date()
	cur.execute(f"SELECT * FROM warn warn_id WHERE( date_out <= '{mydate}' IS NOT active = 0)")
	record = cur.fetchall()
	if len(record) >= 1:
		cur.execute(f"UPDATE warn SET active = 0 WHERE( date_out <= '{mydate}' IS NOT active = 0)")
		print(f"Я снял варны: {len(record)}шт.")
		con.commit()
	else:
		print("Сегодня я не снял варны")

@bot.event
async def on_ready():
    print("Ready")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(func, trigger='cron', hour='00', minute='00')
    scheduler.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    else:
        if bot.user in message.mentions:
            await message.channel.send(f"Мой префикс: ``{str(settings['prefix'])}``\nНужно больше информации? Пропиши: ``{str(settings['prefix'])}help``")
    await bot.process_commands(message)


print ("BOT START")
bot.run(settings['token']) #берем токен из конфига и стартуем