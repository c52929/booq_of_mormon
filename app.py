from flask import Flask, request, abort
from bs4 import BeautifulSoup as bs
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import random
import os

app = Flask(__name__)

# LINE Botの設定
CHANNEL_ACCESS_TOKEN = "UyApRJDDcPq++ysbMZnXe5HKCm6eRHO1L4OHP2ClSE5MlbG53qrfRHbB//kEvz7UqhGGcspnSdFRHOKsBi93BLgONIZ2LyBm0w0StU/kRU2Z1Iiotc/mbuAWYTPqhLIv7dPcH1ybUZHyNff2nQiO8QdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "caa045efa49d895608582a805d061ce0"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

alphabet=[char for char in "abcdefghijklmnopqrstuvwxyz"]
chapter_name=[["1 Nephi","1-ne"],["2 Nephi","2-ne"],["Jacob","jacob"],["Enos","enos"],["Jarom","jarom"],["Omni","omni"],["Words of Mormon","w-of-m"],["Mosiah","mosiah"],["Alma","alma"],["Helaman","hel"],["3 Nephi","3-ne"],["4 Nephi","4-ne"],["Mormon","morm"],["Ether","ether"],["Moroni","moro"]]
number_of_chapter=[22,33,7,1,1,1,1,29,63,16,30,1,9,15,10]

number_of_verse=[20,24,31,38,22,6,22,38,6,22,36,23,42,30,36,39,55,25,24,22,26,31]
number_of_verse+=[32,30,25,35,34,18,11,25,54,25,8,22,26,6,30,13,25,22,21,34,16,6,22,32,30,33,35,32,14,18,21,9,15]
number_of_verse+=[19,35,14,18,77,13,27]
number_of_verse+=[27,15,30,18]
number_of_verse+=[18,41,27,30,15,7,33,21,19,22,29,37,35,12,31,15,20,35,29,26,36,16,39,25,24,39,37,20,47]
number_of_verse+=[33,38,27,20,62,8,27,32,34,32,46,37,31,29,19,21,39,43,36,30,23,35,18,30,17,37,30,14,17,60,38,43,23,41,16,30,47,15,19,26,15,31,54,24,24,41,36,25,30,40,37,40,23,24,35,57,36,41,13,36,21,52,17]
number_of_verse+=[34,14,37,26,52,41,29,28,41,19,38,26,39,31,17,25]
number_of_verse+=[30,19,26,33,26,30,26,25,22,19,41,48,34,27,24,20,25,39,36,46,29,17,14,18,6,21,33,40,9,2,49]
number_of_verse+=[19,29,22,23,24,22,10,41,37]
number_of_verse+=[43,25,28,19,6,30,27,26,35,34,33,41,31,31,34]
number_of_verse+=[4,3,4,3,2,9,48,30,26,34]

# nC=len(number_of_verse) # 239
# nV=np.sum(np.array(number_of_verse)) # 6614
nV=6614

@app.route("/")
def index():
	return "Hello, this is your LINE bot!"

@app.route("/callback", methods=["POST"])
def callback():
	# X-Line-Signatureの検証
	signature = request.headers["X-Line-Signature"]
	body = request.get_data(as_text=True)
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)
	return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	query = event.message.text
	user_id=event.source.user_id
	interpretation=ifcode(query)
	if interpretation==False:
		# new question
		q_num,result = question()
		messages=[
			TextSendMessage(text=f"{result}Reply with the following code:"),
			TextSendMessage(text=encrypt(q_num))
		]
	else:
		# tell answer
		record,chapter,r = split_num(interpretation-1) # -1することに注意
		messages=TextSendMessage(text=f"{chapter_name[record][0]} {chapter}:{r}\n\nhttps://www.churchofjesuschrist.org/study/scriptures/bofm/{chapter_name[record][1]}/{chapter}?lang=jpn&id=p{r}#p{r}")
	try:
		line_bot_api.reply_message(event.reply_token, messages)
	except LineBotApiError as e:
		print(f"Error: {e}")
		line_bot_api.push_message(user_id,TextSendMessage(text="An error has occured. Please try again."))


def question():
	q_num=random.randint(0,nV-1)
	record,chapter,r=split_num(q_num)
	res=requests.get(f"https://www.churchofjesuschrist.org/study/scriptures/bofm/{chapter_name[record][1]}/{chapter}?lang=jpn")
	res.raise_for_status()
	# soup=bs(res.content,"html.parser")
	soup=bs(res.content.decode("utf-8", "ignore"), "html.parser")
	elms=soup.select(f"#p{r}")
	html=str(elms)

	i,text = fromTo(html,0,"","<p","a","</span>",False)
	while 1:
		if html[i:i+6]=="<ruby>":
			i,text = fromTo(html,i,text,"<ruby>","<rb>","</rb>",True)
			i,text = fromTo(html,i,text,"<rt>","</rt>","</ruby>",False)
		elif html[i:i+4]=="</p>" or i>len(html):
			break
		elif html[i:i+3]=="<a ":
			i,text = fromTo(html,i,text,"<a ","</sup>","</a>",True)
		elif html[i:i+5]=="<span":
			i,text = fromTo(html,i,text,"<span","</span",">",False)
		else:
			text+=html[i]
			i+=1
	return q_num,text


def split_num(r):
	chapter=0
	while 1:
		if r-number_of_verse[chapter]>=0:
			r-=number_of_verse[chapter]
			chapter+=1
		else:
			break
	record=0
	while 1:
		if chapter-number_of_chapter[record]>=0:
			chapter-=number_of_chapter[record]
			record+=1
		else:
			break
	chapter+=1
	r+=1
	return record,chapter,r


def fromTo(html,i,text,label,afterFrom,untilBefore,copy):
	i+=len(label)
	while html[i:i+len(afterFrom)]!=afterFrom:
		i+=1
		if i>len(html):
			break
	i+=len(afterFrom)
	while html[i:i+len(untilBefore)]!=untilBefore:
		if html[i:i+6]=="<ruby>":
			i,text = fromTo(html,i,text,"<ruby>","<rb>","</rb>",True)
			i,text = fromTo(html,i,text,"<rt>","</rt>","</ruby>",False)
		else:
			if copy:
				text+=html[i]
			i+=1
			if i>len(html):
				break
	i+=len(untilBefore)
	return i,text


def encrypt(num):
	# 6,7,8進数に変換
	code="df"
	for c in str(convert_pow(num,6)):
		# 6進数: ab cdefgh ijklmn opqrst uvwxyz
		code+=alphabet[6*random.randint(0,3)+int(c)+2]
	code+=alphabet[random.randint(0,1)]
	for c in str(convert_pow(31415-num,8)):
		# 8進数: abcdefgh ijklmnop qrstuvwx yz
		code+=alphabet[8*random.randint(0,2)+int(c)]
	code+=alphabet[random.randint(24,25)]
	for c in str(31415-convert_pow(num,7)):
		# 形は10進数: abcdefghij klmnopqrst uvwxyz
		code+=alphabet[10*random.randint(0,1)+int(c)]
	# print([convert_pow(num,6),convert_pow(9265-num,8),31415-convert_pow(num,7)])
	return f"2{code}veq"


def ifcode(message):
	# 2dfやveqが含まれていない場合、無効
	if "2df" not in message or "veq" not in message:
		return False
	sign=[0,["a","b"],["y","z"],[]]
	i=0
	while 1:
		if message[i:i+3]=="2df":
			i+=3
			break
		i+=1
	sep=[""]
	while i+2<len(message):
		if len(sep)==3 and message[i:i+3]=="veq":
			break
		if message[i] in sign[len(sep)]:
			sep.append("")
		else:
			sep[-1]+=message[i]
		i+=1
	# print(sep)

	nums=[0,0,0]
	for c in sep[0]:
		nums[0]=10*nums[0]+(alphabet.index(c)-2)%6
	for c in sep[1]:
		nums[1]=10*nums[1]+alphabet.index(c)%8
	for c in sep[2]:
		nums[2]=10*nums[2]+alphabet.index(c)%10
	# print(nums)
	nums[2]=31415-nums[2]

	nums=list(map(str,nums))
	nums_dec=[0,0,0]
	nums_base=[6,8,7]
	for i in range(3):
		for j in range(len(nums[i])):
			nums_dec[i]+=int(nums[i][len(nums[i])-j-1])*pow(nums_base[i],j)
	nums_dec[1]=31415-nums_dec[1]
	# print(nums_dec)

	if nums_dec[0]==nums_dec[1] or nums_dec[0]==nums_dec[2]:
		return nums_dec[0]+1 # +1していることに注意
	elif nums_dec[1]==nums_dec[2]:
		return nums_dec[1]+1 # +1していることに注意
	else:
		return False


def convert_pow(num,base):
	rem=num
	code=0
	for i in range(6):
		power=pow(base,(5-i))
		code*=10
		if rem>=power:
			avail=rem//power
			code+=avail
			rem-=power*avail
	return code


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))  # 環境変数PORTが設定されていない場合は5000をデフォルトに
	app.run(host="0.0.0.0", port=port)
